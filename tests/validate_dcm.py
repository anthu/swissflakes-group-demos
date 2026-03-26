#!/usr/bin/env python3
"""
DCM Data Product Validation Test Suite

Validates that each data product follows the canonical DCM layout:
- Flat directory structure (no dcm/ subfolder)
- Manifest with DEV/PROD targets, templating, unique names
- Infrastructure SQL with {{env_suffix}} templating
- Minimal dbt profiles.yml
- No hardcoded account/user values

Usage:
    python tests/validate_dcm.py                     # validate all DPs
    python tests/validate_dcm.py customers            # validate single DP
    python tests/validate_dcm.py customers fleet      # validate multiple DPs
"""

import os
import sys
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PRODUCTS_DIR = REPO_ROOT / "data_products"

SOURCE_DPS = ["customers", "shipments", "fleet", "locations", "orders", "products", "transactions", "merchants"]
ENTERPRISE_DPS = ["fulfillment", "customer_360"]
CONSUMER_DPS = ["revenue_analytics", "compliance"]
PLATFORM_DP = "platform"

ALL_DPS = SOURCE_DPS + ENTERPRISE_DPS + CONSUMER_DPS + [PLATFORM_DP]

DP_TYPES = {}
for dp in SOURCE_DPS:
    DP_TYPES[dp] = "SOURCE"
for dp in ENTERPRISE_DPS:
    DP_TYPES[dp] = "ENTERPRISE"
for dp in CONSUMER_DPS:
    DP_TYPES[dp] = "CONSUMER"
DP_TYPES[PLATFORM_DP] = "PLATFORM"

HARDCODED_PATTERNS = [
    re.compile(r"HE80908", re.IGNORECASE),
    re.compile(r"\bANTON\b"),
    re.compile(r"\bahuck\b"),
]

FORBIDDEN_PROFILE_KEYS = {"account", "user", "password", "warehouse", "threads", "authenticator"}
REQUIRED_PROFILE_KEYS = {"type", "database", "role", "schema"}


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""


@dataclass
class DPValidation:
    dp_name: str
    results: list = field(default_factory=list)

    def add(self, name: str, passed: bool, message: str = ""):
        self.results.append(TestResult(name, passed, message))

    @property
    def pass_count(self):
        return sum(1 for r in self.results if r.passed)

    @property
    def fail_count(self):
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self):
        return len(self.results)


def db_name(dp_name: str) -> str:
    if dp_name == PLATFORM_DP:
        return "SWISSFLAKES_ADMIN"
    return dp_name.upper()


def validate_structure(dp: str, v: DPValidation):
    dp_dir = DATA_PRODUCTS_DIR / dp
    manifest = dp_dir / "manifest.yml"
    sources_dir = dp_dir / "sources"
    defs_dir = sources_dir / "definitions"
    old_dcm_dir = dp_dir / "dcm"

    v.add("manifest_exists", manifest.is_file(),
           f"manifest.yml at {manifest}" if manifest.is_file() else f"MISSING: {manifest}")

    v.add("sources_dir_exists", sources_dir.is_dir(),
           "" if sources_dir.is_dir() else f"MISSING: {sources_dir}")

    v.add("definitions_dir_exists", defs_dir.is_dir(),
           "" if defs_dir.is_dir() else f"MISSING: {defs_dir}")

    if defs_dir.is_dir():
        sql_files = list(defs_dir.glob("*.sql"))
        v.add("has_sql_definitions", len(sql_files) > 0,
               f"Found {len(sql_files)} SQL files" if sql_files else "No .sql files in definitions/")

    v.add("no_dcm_subdir", not old_dcm_dir.is_dir(),
           "" if not old_dcm_dir.is_dir() else f"STALE: {old_dcm_dir} still exists")

    if dp != PLATFORM_DP:
        dbt_dir = sources_dir / "dbt"
        v.add("dbt_dir_exists", dbt_dir.is_dir(),
               "" if dbt_dir.is_dir() else f"MISSING: {dbt_dir}")


def validate_manifest(dp: str, v: DPValidation):
    manifest_path = DATA_PRODUCTS_DIR / dp / "manifest.yml"
    if not manifest_path.is_file():
        v.add("manifest_readable", False, "Cannot read manifest - file missing")
        return

    try:
        with open(manifest_path) as f:
            m = yaml.safe_load(f)
    except Exception as e:
        v.add("manifest_readable", False, f"YAML parse error: {e}")
        return

    v.add("manifest_version", m.get("manifest_version") == 2,
           f"Got: {m.get('manifest_version')}")

    v.add("manifest_type", str(m.get("type", "")).upper() == "DCM_PROJECT",
           f"Got: {m.get('type')}")

    targets = m.get("targets", {})
    v.add("has_dev_target", "DEV" in targets,
           "DEV target present" if "DEV" in targets else "MISSING DEV target")

    v.add("has_prod_target", "PROD" in targets,
           "PROD target present" if "PROD" in targets else "MISSING PROD target")

    DB = db_name(dp)

    for tgt_name, tgt in targets.items():
        acct = str(tgt.get("account_identifier", ""))
        is_hardcoded = any(p.search(acct) for p in HARDCODED_PATTERNS)
        v.add(f"{tgt_name}_account_not_hardcoded", not is_hardcoded,
               f"{tgt_name}: {acct}" if is_hardcoded else "")

        proj = str(tgt.get("project_name", ""))
        not_generic = "DATA_PRODUCT" not in proj
        v.add(f"{tgt_name}_project_name_unique", not_generic,
               f"{tgt_name}: {proj}" if not not_generic else "")

        if dp == PLATFORM_DP:
            v.add(f"{tgt_name}_project_name_pattern", "PLATFORM" in proj,
                   f"{tgt_name}: {proj}")
        else:
            expected_suffix = f"DCM.DP_{DB}"
            v.add(f"{tgt_name}_project_name_pattern", expected_suffix in proj,
                   f"{tgt_name}: {proj} (expected *{expected_suffix})")

        owner = str(tgt.get("project_owner", ""))
        if dp == PLATFORM_DP:
            v.add(f"{tgt_name}_owner_not_accountadmin",
                   tgt_name == "DEV" or owner != "ACCOUNTADMIN",
                   f"{tgt_name}: {owner}")
        else:
            v.add(f"{tgt_name}_owner_is_dp_role",
                   owner != "ACCOUNTADMIN" and f"DP_{DB}" in owner,
                   f"{tgt_name}: {owner}")

        v.add(f"{tgt_name}_has_project_comment", "project_comment" in tgt,
               "" if "project_comment" in tgt else f"{tgt_name}: missing project_comment")

        v.add(f"{tgt_name}_has_templating_config", "templating_config" in tgt,
               "" if "templating_config" in tgt else f"{tgt_name}: missing templating_config")

    templating = m.get("templating", {})
    v.add("has_templating", bool(templating),
           "" if templating else "MISSING templating section")

    defaults = templating.get("defaults", {})
    for key in ["dp_name", "dp_type", "dp_description"]:
        v.add(f"defaults_has_{key}", key in defaults,
               f"defaults.{key} = {defaults.get(key, 'MISSING')}")

    configs = templating.get("configurations", {})
    v.add("has_dev_config", "DEV" in configs,
           "" if "DEV" in configs else "MISSING DEV configuration")
    v.add("has_prod_config", "PROD" in configs,
           "" if "PROD" in configs else "MISSING PROD configuration")

    if "DEV" in configs:
        dev_suffix = configs["DEV"].get("env_suffix", None)
        v.add("dev_env_suffix", dev_suffix == "_DEV",
               f"DEV env_suffix = {dev_suffix!r}")

    if "PROD" in configs:
        prod_suffix = configs["PROD"].get("env_suffix", None)
        v.add("prod_env_suffix", prod_suffix == "",
               f"PROD env_suffix = {prod_suffix!r}")


def validate_infrastructure_sql(dp: str, v: DPValidation):
    infra_path = DATA_PRODUCTS_DIR / dp / "sources" / "definitions" / "01_infrastructure.sql"
    if not infra_path.is_file():
        v.add("infra_sql_exists", False, f"MISSING: {infra_path}")
        return

    content = infra_path.read_text()
    DB = db_name(dp)

    bare_db_pattern = re.compile(rf"\b{DB}\b(?!\{{)")
    env_suffix_pattern = re.compile(rf"{DB}\{{\{{env_suffix\}}\}}")

    has_env_suffix = bool(env_suffix_pattern.search(content))
    v.add("infra_uses_env_suffix", has_env_suffix,
           "" if has_env_suffix else f"No {DB}{{{{env_suffix}}}} found")

    lines_with_bare_db = []
    for i, line in enumerate(content.splitlines(), 1):
        line_stripped = line.strip()
        if line_stripped.startswith("--"):
            continue
        if bare_db_pattern.search(line) and not env_suffix_pattern.search(line):
            lines_with_bare_db.append(i)

    v.add("no_bare_db_names", len(lines_with_bare_db) == 0,
           f"Lines with bare {DB}: {lines_with_bare_db[:5]}" if lines_with_bare_db else "")

    for p in HARDCODED_PATTERNS:
        matches = p.findall(content)
        v.add(f"infra_no_{p.pattern}", len(matches) == 0,
               f"Found {len(matches)} matches for {p.pattern}" if matches else "")


def validate_dbt_sql(dp: str, v: DPValidation):
    if dp == PLATFORM_DP:
        return

    dbt_sql_path = DATA_PRODUCTS_DIR / dp / "sources" / "definitions" / "02_dbt.sql"
    if not dbt_sql_path.is_file():
        v.add("dbt_sql_exists", False, f"MISSING: {dbt_sql_path}")
        return

    content = dbt_sql_path.read_text()
    DB = db_name(dp)

    env_suffix_in_db = re.search(rf"{DB}\{{\{{env_suffix\}}\}}", content)
    v.add("dbt_sql_uses_env_suffix", bool(env_suffix_in_db),
           "" if env_suffix_in_db else f"No {DB}{{{{env_suffix}}}} in DEFINE DBT PROJECT")


def validate_profiles(dp: str, v: DPValidation):
    if dp == PLATFORM_DP:
        return

    profiles_path = DATA_PRODUCTS_DIR / dp / "sources" / "dbt" / "profiles.yml"
    if not profiles_path.is_file():
        v.add("profiles_exists", False, f"MISSING: {profiles_path}")
        return

    try:
        with open(profiles_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        v.add("profiles_readable", False, f"YAML parse error: {e}")
        return

    for profile_name, profile in data.items():
        outputs = profile.get("outputs", {})
        for output_name, output_cfg in outputs.items():
            keys = set(output_cfg.keys())

            for forbidden in FORBIDDEN_PROFILE_KEYS:
                v.add(f"profiles_no_{forbidden}",
                       forbidden not in keys,
                       f"profiles.yml has forbidden key: {forbidden}" if forbidden in keys else "")

            for required in REQUIRED_PROFILE_KEYS:
                v.add(f"profiles_has_{required}",
                       required in keys,
                       f"profiles.yml missing required key: {required}" if required not in keys else "")


def validate_no_hardcoded(dp: str, v: DPValidation):
    dp_dir = DATA_PRODUCTS_DIR / dp
    for fpath in dp_dir.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix not in (".yml", ".yaml", ".sql", ".md"):
            continue
        if ".snowflake" in str(fpath) or "out/" in str(fpath):
            continue

        try:
            content = fpath.read_text()
        except Exception:
            continue

        rel = fpath.relative_to(dp_dir)
        for p in HARDCODED_PATTERNS:
            if p.search(content):
                v.add(f"no_hardcoded_{p.pattern}_in_{rel}",
                       False,
                       f"Found {p.pattern} in {rel}")


def validate_dp(dp: str) -> DPValidation:
    v = DPValidation(dp_name=dp)
    validate_structure(dp, v)
    validate_manifest(dp, v)
    validate_infrastructure_sql(dp, v)
    validate_dbt_sql(dp, v)
    validate_profiles(dp, v)
    validate_no_hardcoded(dp, v)
    return v


def print_results(validations: list[DPValidation]):
    total_pass = 0
    total_fail = 0

    for v in validations:
        total_pass += v.pass_count
        total_fail += v.fail_count

        status = "PASS" if v.fail_count == 0 else "FAIL"
        print(f"\n{'='*60}")
        print(f"  {v.dp_name.upper():30s} [{status}] {v.pass_count}/{v.total} passed")
        print(f"{'='*60}")

        for r in v.results:
            icon = "✓" if r.passed else "✗"
            msg = f"  {r.message}" if r.message else ""
            if not r.passed:
                print(f"  {icon} {r.name}{msg}")

        if v.fail_count == 0:
            print("  All tests passed.")

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_pass}/{total_pass + total_fail} passed, {total_fail} failed")
    print(f"{'='*60}")

    return total_fail == 0


def main():
    dps = sys.argv[1:] if len(sys.argv) > 1 else ALL_DPS

    for dp in dps:
        if dp not in ALL_DPS:
            print(f"Unknown data product: {dp}")
            print(f"Available: {', '.join(ALL_DPS)}")
            sys.exit(1)

    validations = [validate_dp(dp) for dp in dps]
    all_passed = print_results(validations)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
