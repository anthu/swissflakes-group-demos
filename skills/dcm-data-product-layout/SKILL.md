# DCM Data Product Layout — Canonical Reference

## Directory Structure

```
data_products/{dp_name}/
  manifest.yml                          # DCM project manifest (at DP root, NOT in dcm/ subfolder)
  sources/
    definitions/
      01_infrastructure.sql             # Schemas, roles, grants (with {{env_suffix}})
      02_dbt.sql                        # DEFINE DBT PROJECT (with {{env_suffix}})
      02_access.sql                     # Platform only: platform roles and warehouse grants
    dbt/
      dbt_project.yml
      profiles.yml                      # Minimal: type, database, role, schema ONLY
      models/
      seeds/
      macros/
```

Platform DP (`data_products/platform/`) has no `dbt/` directory or `02_dbt.sql` — it has `02_access.sql` instead.

## manifest.yml Template

### Source / Enterprise / Consumer DP

```yaml
manifest_version: 2
type: DCM_PROJECT

default_target: PROD

templating:
  defaults:
    dp_type: "SOURCE"                   # or "ENTERPRISE" or "CONSUMER"
    dp_name: "{DB}"                     # e.g. "CUSTOMERS", "FULFILLMENT"
    dp_description: "Human-readable description of this data product"

  configurations:
    DEV:
      env_suffix: "_DEV"
    PROD:
      env_suffix: ""

targets:
  DEV:
    account_identifier: "{{ env_var('SNOWFLAKE_ACCOUNT_DEV') }}"
    project_name: '{DB}_DEV.DCM.DP_{DB}'
    project_owner: DP_{DB}_DEV_OWNER
    project_comment: "{{dp_type}} Data Product: {{dp_description}}"
    templating_config: DEV

  PROD:
    account_identifier: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
    project_name: '{DB}.DCM.DP_{DB}'
    project_owner: DP_{DB}_OWNER
    project_comment: "{{dp_type}} Data Product: {{dp_description}}"
    templating_config: PROD
```

### Platform DP

```yaml
manifest_version: 2
type: DCM_PROJECT

default_target: PROD

templating:
  defaults:
    dp_type: "PLATFORM"
    dp_name: "SWISSFLAKES_ADMIN"
    dp_description: "Platform administration including warehouses, governance tags, and RBAC roles"

  configurations:
    DEV:
      env_suffix: "_DEV"
    PROD:
      env_suffix: ""

targets:
  DEV:
    account_identifier: "{{ env_var('SNOWFLAKE_ACCOUNT_DEV') }}"
    project_name: 'SWISSFLAKES_ADMIN_DEV.DCM.PLATFORM'
    project_owner: ACCOUNTADMIN
    project_comment: "{{dp_type}} Data Product: {{dp_description}}"
    templating_config: DEV

  PROD:
    account_identifier: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
    project_name: 'SWISSFLAKES_ADMIN.DCM.PLATFORM'
    project_owner: SWISSFLAKES_PLATFORM_ADMIN
    project_comment: "{{dp_type}} Data Product: {{dp_description}}"
    templating_config: PROD
```

## Manifest Rules

| Field | Rule |
|---|---|
| `manifest_version` | Always `2` |
| `type` | Always `DCM_PROJECT` |
| `default_target` | `PROD` |
| `account_identifier` | NEVER hardcode. Use `{{ env_var('SNOWFLAKE_ACCOUNT') }}` for PROD, `{{ env_var('SNOWFLAKE_ACCOUNT_DEV') }}` for DEV |
| `project_name` | `{DB}.DCM.DP_{DB}` for data products, `{DB}.DCM.PLATFORM` for platform. NEVER use generic `DATA_PRODUCT` |
| `project_owner` | `DP_{DB}_OWNER` for data products (NEVER `ACCOUNTADMIN`). Platform PROD uses `SWISSFLAKES_PLATFORM_ADMIN` |
| `project_comment` | Use `"{{dp_type}} Data Product: {{dp_description}}"` |
| `templating_config` | Must reference a configuration name (`DEV` or `PROD`) |
| `templating.defaults` | Must include `dp_type`, `dp_name`, `dp_description` |
| `templating.configurations` | Must include `DEV` (env_suffix: `"_DEV"`) and `PROD` (env_suffix: `""`) |

## 01_infrastructure.sql Template

Every DB name and role name must use `{{env_suffix}}`. Use `{{dp_name}}` in COMMENT strings.

```sql
DEFINE SCHEMA {DB}{{env_suffix}}.RAW;
DEFINE SCHEMA {DB}{{env_suffix}}.STAGING;
DEFINE SCHEMA {DB}{{env_suffix}}.MARTS;

DEFINE ROLE DP_{DB}{{env_suffix}}_OWNER
    COMMENT = 'Full DB control for {{dp_name}} data product';

DEFINE ROLE DP_{DB}{{env_suffix}}_WRITER
    COMMENT = 'RAW + STAGING read/write for {{dp_name}}';

DEFINE ROLE DP_{DB}{{env_suffix}}_READER
    COMMENT = 'MARTS read-only for {{dp_name}}';

GRANT ROLE DP_{DB}{{env_suffix}}_READER TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT ROLE DP_{DB}{{env_suffix}}_WRITER TO ROLE DP_{DB}{{env_suffix}}_OWNER;
GRANT ROLE DP_{DB}{{env_suffix}}_OWNER TO ROLE SWISSFLAKES_PLATFORM_ADMIN;

GRANT USAGE ON DATABASE {DB}{{env_suffix}} TO ROLE DP_{DB}{{env_suffix}}_READER;
GRANT USAGE ON SCHEMA {DB}{{env_suffix}}.MARTS TO ROLE DP_{DB}{{env_suffix}}_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA {DB}{{env_suffix}}.MARTS TO ROLE DP_{DB}{{env_suffix}}_READER;
GRANT SELECT ON ALL VIEWS IN SCHEMA {DB}{{env_suffix}}.MARTS TO ROLE DP_{DB}{{env_suffix}}_READER;

GRANT USAGE ON SCHEMA {DB}{{env_suffix}}.RAW TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT USAGE ON SCHEMA {DB}{{env_suffix}}.STAGING TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {DB}{{env_suffix}}.RAW TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {DB}{{env_suffix}}.STAGING TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT SELECT ON ALL TABLES IN SCHEMA {DB}{{env_suffix}}.RAW TO ROLE DP_{DB}{{env_suffix}}_WRITER;
GRANT SELECT ON ALL TABLES IN SCHEMA {DB}{{env_suffix}}.STAGING TO ROLE DP_{DB}{{env_suffix}}_WRITER;

GRANT CREATE TABLE, CREATE VIEW ON SCHEMA {DB}{{env_suffix}}.RAW TO ROLE DP_{DB}{{env_suffix}}_OWNER;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA {DB}{{env_suffix}}.STAGING TO ROLE DP_{DB}{{env_suffix}}_OWNER;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA {DB}{{env_suffix}}.MARTS TO ROLE DP_{DB}{{env_suffix}}_OWNER;
```

## 02_dbt.sql Template

```sql
DEFINE DBT PROJECT {DB}{{env_suffix}}.DCM.DBT_{DB}
  FROM 'sources/dbt'
  DEFAULT_TARGET = 'prod';
```

## profiles.yml (Minimal)

Only 4 keys allowed. NEVER include `account`, `user`, `password`, `warehouse`, `threads`, `authenticator`.

```yaml
{profile_name}:
  target: prod
  outputs:
    prod:
      type: snowflake
      database: {DB}
      role: DP_{DB}_OWNER
      schema: STAGING
```

## Deployment Commands

```bash
# Create new project (idempotent)
snow dcm create {DB}.DCM.DP_{DB} --if-not-exists -c {connection}

# Deploy from local directory
SNOWFLAKE_ACCOUNT={ACCOUNT_ID} snow dcm deploy {DB}.DCM.DP_{DB} \
  -c {connection} \
  --alias "{alias}" \
  --from /path/to/data_products/{dp_name}

# If migrating from old project name, drop old first
snow dcm drop {DB}.DCM.DATA_PRODUCT -c {connection}
```

## Validation

Run `tests/validate_dcm.py` to check compliance:

```bash
python3 tests/validate_dcm.py                  # all DPs
python3 tests/validate_dcm.py customers fleet   # specific DPs
```

Checks: flat structure, manifest schema, `{{env_suffix}}` usage, minimal profiles.yml, no hardcoded values (account IDs, usernames).

## Anti-Patterns

| Anti-Pattern | Correct Pattern |
|---|---|
| `dcm/` subfolder nesting | `manifest.yml` at DP root |
| `project_name: 'DB.DCM.DATA_PRODUCT'` | `project_name: 'DB.DCM.DP_DB'` |
| `account_identifier: ACCT_LOCATOR` | `account_identifier: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"` |
| `project_owner: ACCOUNTADMIN` | `project_owner: DP_{DB}_OWNER` |
| Bare `CUSTOMERS.RAW` in SQL | `CUSTOMERS{{env_suffix}}.RAW` |
| Bare DB name in COMMENT strings | `{{dp_name}}` template variable |
| `account:`, `user:`, `warehouse:` in profiles.yml | Remove — only `type`, `database`, `role`, `schema` |
| Single PROD target only | Both `DEV` and `PROD` targets with `templating_config` |

## Comparison with Other IaC Tools

DCM is Snowflake-native declarative infrastructure-as-code using `DEFINE` instead of `CREATE`.

For teams using Terraform instead of DCM, the Snowflake provider is:

```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "2.14.0"
    }
  }
}

provider "snowflake" {
  # Configuration options
}
```

DCM advantages over Terraform for Snowflake:
- Native Jinja templating with `{{env_suffix}}` for multi-environment
- `DEFINE DBT PROJECT` embeds dbt natively
- `snow dcm deploy` handles drift detection and idempotent deployments
- No state file management required
