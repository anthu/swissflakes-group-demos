---
name: dcm-ephemeral-pr-environments
description: "Set up GitHub Actions pipelines that deploy ephemeral Snowflake test environments per pull request using DCM. Each PR gets an isolated zero-copy clone database with a DCM project deployed into it, automatically torn down on close/merge. Use this skill whenever someone asks about CI/CD for Snowflake DCM projects, PR-based test environments, ephemeral databases, GitHub Actions + Snowflake integration, or automating DCM plan/deploy/test in a pipeline — even if they don't use these exact terms."
tools:
  - Bash
  - Read
  - Write
  - Edit
  - ask_user_question
  - snowflake_sql_execute
---

# DCM Ephemeral PR Environments

Two GitHub Actions workflows that give every pull request its own isolated Snowflake environment:

1. **Deploy** (PR opened/updated): `PARSE_MANIFEST → PLAN → DROP_DETECTION → DEPLOY → REFRESH → TEST → COMMENT`
2. **Teardown** (PR closed/merged): `DROP project → DROP database → DROP roles → COMMENT`

Each PR gets a zero-copy clone of the source database (`{SOURCE_DB}_PR{N}`) with a full DCM project deployed into it.

## Prerequisites

### Snowflake

The CI role needs powerful account-level grants because it creates and destroys databases and roles dynamically:

```sql
GRANT CREATE DATABASE ON ACCOUNT TO ROLE <ci_role>;
GRANT CREATE ROLE ON ACCOUNT TO ROLE <ci_role>;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <ci_role>;
```

Also required:
- **Service user** (TYPE=SERVICE) with a programmatic access token (PAT)
- **Warehouse** with USAGE + OPERATE to the CI role
- **EAI grant** (if DCM project uses dbt GitHub packages): `GRANT USAGE ON INTEGRATION <eai> TO ROLE <ci_role>`
- **Source DB ownership** — objects must NOT be owned by ACCOUNTADMIN. `CREATE DATABASE ... CLONE` preserves ownership, so if ACCOUNTADMIN owns objects, the CI role can't access them after cloning. Transfer ownership first.
- **Network policy** — allow GitHub Actions IPs via `SNOWFLAKE.NETWORK_SECURITY.GITHUBACTIONS_GLOBAL`

### GitHub Secrets & Variables

| Type | Name | Purpose |
|------|------|---------|
| Secret | `DEPLOYER_PAT` | Snowflake programmatic access token |
| Variable | `SNOWFLAKE_USER` | Service user name |
| Variable | `SNOWFLAKE_ACCOUNT` | Account identifier (e.g. `abc12345.us-east-1`) |
| Variable | `SNOWFLAKE_CI_ROLE` | CI role name |
| Variable | `SNOWFLAKE_WAREHOUSE` | Warehouse name |

## Implementation Steps

### Step 1: Gather Information

Infer what you can from the repo (look for `manifest.yml` files, existing connections, Terraform configs). Ask the user to confirm or fill gaps:

1. **DCM project path** — relative path within the repo (e.g. `data_products/sfg_logistics/`)
2. **Source database name** — the production database to clone from
3. **CI role name** and **source DB owner role**
4. **Whether the project uses EAI** (check for `EXTERNAL_ACCESS_INTEGRATIONS` in definition SQL files)

### Step 2: Fix Source Database Ownership

This step matters because `CREATE DATABASE ... CLONE` copies ownership verbatim. If objects are owned by ACCOUNTADMIN, the CI role won't be able to read or modify them in the clone.

```sql
SELECT table_schema, table_name, table_type, COALESCE(table_owner, 'NO_OWNER') as owner
FROM {source_db}.information_schema.tables
WHERE table_owner = 'ACCOUNTADMIN' OR table_owner IS NULL;
```

If results are found, transfer ownership — see reference/deploy-workflow.md for the full grant pattern covering DB, schemas, tables, views, dynamic tables, and stages.

### Step 3: Add PR_EPHEMERAL Target to Manifest

DCM's `project_name` field does NOT support Jinja2 templating. Use a sed placeholder instead — see reference/manifest-config.md for the pattern. The key insight: `___PR_NUMBER___` gets replaced by `sed` in every workflow job that reads the manifest.

### Step 4: Create Workflow Files

1. `.github/requirements-snowcli.txt` containing `snowflake-cli`
2. `.github/workflows/dcm_pr_ephemeral_deploy.yml` — see reference/deploy-workflow.md
3. `.github/workflows/dcm_pr_ephemeral_teardown.yml` — see reference/teardown-workflow.md

When adapting the templates, replace `<SOURCE_DB>` and `<DCM_PROJECT_PATH>` placeholders with the actual values from Step 1.

### Step 5: Verify Grants and Test

```sql
SHOW GRANTS TO ROLE <ci_role>;
```

Confirm: CREATE DATABASE, CREATE ROLE, MANAGE GRANTS on ACCOUNT; USAGE+OPERATE on warehouse; USAGE on EAI (if applicable).

Then open a PR that modifies files in the DCM project path and verify the full lifecycle: deploy on open, teardown on close/merge.

## Key Patterns to Get Right

**Deploy alias must be unique per run** — using just `pr-{N}` causes "alias already exists" on re-runs. Include run number and git SHA: `pr-{N}-run{RUN}-{SHA}`.

**Ownership transfer after clone** — the clone step and 6 ownership grants (DB, schemas, tables, views, dynamic tables, stages) must happen before `snow dcm create/plan`. Without this, you get `Schema 'X.DCM' does not exist` or `Insufficient privileges` errors.

**sed in every job** — each GitHub Actions job gets a fresh checkout. The `sed -i "s/___PR_NUMBER___/..."` replacement must run in every job that reads the manifest.

**tee for deploy output** — capturing output in a variable (`output=$(command)`) hides it from GitHub Actions logs. Use `command 2>&1 | tee /tmp/out.txt` and `${PIPESTATUS[0]}` for the exit code.

**plan.json schema** — the file is at `out/plan.json` (not `out/plan_metadata.json`). Schema: `.changeset[].type` (CREATE/ALTER/DROP) and `.changeset[].object_id.domain` (ROLE/DATABASE/TABLE/etc.). See reference/plan-json-schema.md for jq recipes.

## Terraform Integration

If managing infrastructure with Terraform, codify the EAI and its grant — see the Terraform snippet in reference/deploy-workflow.md or use this pattern:

```terraform
resource "snowflake_network_rule" "github_egress" {
  name       = "GITHUB_EGRESS_RULE"
  database   = "<admin_db>"
  schema     = "<admin_schema>"
  type       = "HOST_PORT"
  mode       = "EGRESS"
  value_list = ["github.com", "codeload.github.com"]
}

resource "snowflake_execute" "github_eai" {
  execute = <<-SQL
    CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION <eai_name>
      ALLOWED_NETWORK_RULES = (${snowflake_network_rule.github_egress.fully_qualified_name})
      ENABLED = TRUE
  SQL
  revert = "DROP EXTERNAL ACCESS INTEGRATION IF EXISTS <eai_name>"
}

resource "snowflake_execute" "github_eai_grant_ci" {
  execute    = "GRANT USAGE ON INTEGRATION <eai_name> TO ROLE <ci_role>"
  revert     = "REVOKE USAGE ON INTEGRATION <eai_name> FROM ROLE <ci_role>"
  depends_on = [snowflake_execute.github_eai]
}
```
