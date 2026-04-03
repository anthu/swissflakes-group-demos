---
name: dcm-ephemeral-pr-environments
description: "Create GitHub Actions pipelines that deploy ephemeral Snowflake test environments per PR using DCM (Database Change Management). Environments are created on PR open and torn down on PR close/merge. Triggers: ephemeral environment, PR environment, test environment, DCM CI/CD, DCM GitHub Actions, ephemeral database, PR pipeline, zero-copy clone CI."
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - ask_user_question
  - snowflake_sql_execute
---

# DCM Ephemeral PR Environments

Creates GitHub Actions workflows that deploy isolated Snowflake test environments per pull request using Snowflake DCM (Database Change Management). Environments are automatically created when a PR is opened and torn down when the PR is closed or merged.

## When to Use

- User wants CI/CD for Snowflake DCM projects triggered by pull requests
- User wants ephemeral/isolated test environments per PR
- User wants automatic cleanup of Snowflake objects when PRs are closed
- User asks about GitHub Actions + Snowflake DCM integration
- User wants zero-copy clone based test environments

## Architecture Overview

Two GitHub Actions workflows work together:

1. **Deploy Workflow** (on `pull_request: [opened, synchronize, reopened]`):
   `PARSE_MANIFEST → PLAN → DROP_DETECTION → DEPLOY → REFRESH_DYNAMIC_TABLES → TEST_EXPECTATIONS → COMMENT_ON_PR`

2. **Teardown Workflow** (on `pull_request: [closed]`):
   `TEARDOWN → COMMENT_ON_PR`

Each PR gets its own isolated Snowflake database (`{SOURCE_DB}_PR{N}`) created via zero-copy clone, with a DCM project deployed into it.

## Prerequisites

### Snowflake Setup

1. **Service user** (TYPE=SERVICE) with a programmatic access token (PAT)
2. **CI role** with these account-level grants:
   ```sql
   GRANT CREATE DATABASE ON ACCOUNT TO ROLE <ci_role>;
   GRANT CREATE ROLE ON ACCOUNT TO ROLE <ci_role>;
   GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <ci_role>;
   ```
3. **Warehouse** with USAGE + OPERATE granted to the CI role
4. **External Access Integrations** — if the DCM project uses dbt packages from GitHub, an EAI must exist and USAGE must be granted to the CI role:
   ```sql
   GRANT USAGE ON INTEGRATION <eai_name> TO ROLE <ci_role>;
   ```
5. **Source database ownership** — all objects in the source database must be owned by a role the CI role can impersonate (not ACCOUNTADMIN), because `CREATE DATABASE ... CLONE` preserves the original ownership. After cloning, the workflow transfers ownership to the CI role.
6. **Network policy** — allow GitHub Actions IP ranges (use `SNOWFLAKE.NETWORK_SECURITY.GITHUBACTIONS_GLOBAL`)

### GitHub Setup

**Secrets:**
- `DEPLOYER_PAT` — the Snowflake programmatic access token

**Variables:**
- `SNOWFLAKE_USER` — service user name
- `SNOWFLAKE_ACCOUNT` — account identifier (e.g., `abc12345.us-east-1`)
- `SNOWFLAKE_CI_ROLE` — the CI role name
- `SNOWFLAKE_WAREHOUSE` — warehouse name

### DCM Manifest Configuration

The manifest must use a sed placeholder `___PR_NUMBER___` because `project_name` does NOT support Jinja2 templating:

```yaml
targets:
  PR_EPHEMERAL:
    account_identifier: '<account>'
    project_name: '<SOURCE_DB>_PR___PR_NUMBER___'
    project_owner: '<ci_role>'
    templating_config:
      variables:
        env: 'PR___PR_NUMBER___'
```

The workflow resolves `___PR_NUMBER___` with:
```bash
sed -i "s/___PR_NUMBER___/${PR_NUMBER}/g" manifest.yml
```

## Implementation Steps

### Step 1: Gather Information

Ask the user for:
1. **Repository path** — where is the GitHub repo cloned?
2. **DCM project path** — relative path to the DCM project within the repo (e.g., `data_products/sfg_logistics/`)
3. **Source database name** — the production database to clone from
4. **Snowflake account identifier**
5. **CI role name** — the role that will own ephemeral environments
6. **Warehouse name**
7. **Source DB owner role** — the role that owns objects in the source database
8. **Target branch** — usually `main`
9. **Whether the project uses External Access Integrations** (dbt GitHub packages, etc.)

### Step 2: Validate Source Database Ownership

All objects in the source database should NOT be owned by ACCOUNTADMIN. Check and fix:

```sql
-- Check ownership
SELECT table_schema, table_name, table_type,
       COALESCE(table_owner, 'NO_OWNER') as owner
FROM {source_db}.information_schema.tables
WHERE table_owner = 'ACCOUNTADMIN' OR table_owner IS NULL;
```

Transfer ownership if needed:
```sql
GRANT OWNERSHIP ON DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL TABLES IN DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL VIEWS IN DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL DYNAMIC TABLES IN DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL STAGES IN DATABASE {source_db} TO ROLE {owner_role} COPY CURRENT GRANTS;
```

### Step 3: Update DCM Manifest

Add the `PR_EPHEMERAL` target to `manifest.yml` using the `___PR_NUMBER___` placeholder pattern.

### Step 4: Create pip requirements file

Create `.github/requirements-snowcli.txt`:
```
snowflake-cli
```

### Step 5: Create Deploy Workflow

Create `.github/workflows/dcm_pr_ephemeral_deploy.yml` — see reference/deploy-workflow.md for the complete template.

Key patterns in the deploy workflow:
- **sed placeholder resolution** in every job that reads the manifest
- **Zero-copy clone + ownership transfer** before DCM plan:
  ```bash
  snow sql -q "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CLONE ${SOURCE_DB}" -x
  snow sql -q "GRANT OWNERSHIP ON DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  snow sql -q "GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  snow sql -q "GRANT OWNERSHIP ON ALL TABLES IN DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  snow sql -q "GRANT OWNERSHIP ON ALL VIEWS IN DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  snow sql -q "GRANT OWNERSHIP ON ALL DYNAMIC TABLES IN DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  snow sql -q "GRANT OWNERSHIP ON ALL STAGES IN DATABASE ${DB_NAME} TO ROLE ${CI_ROLE} COPY CURRENT GRANTS" -x
  ```
- **plan.json parsing** with correct schema: `.changeset[].type` and `.changeset[].object_id.domain`
- **Deploy alias uniqueness**: `pr-{PR_NUMBER}-run{RUN_NUMBER}-{SHORT_SHA}`
- **tee pattern** for deploy output capture: `snow dcm deploy ... 2>&1 | tee /tmp/output.txt` + `${PIPESTATUS[0]}`
- **pip caching** via `actions/setup-python@v5` with `cache: 'pip'`

### Step 6: Create Teardown Workflow

Create `.github/workflows/dcm_pr_ephemeral_teardown.yml` — see reference/teardown-workflow.md for the complete template.

Key patterns in the teardown workflow:
- Triggered on `pull_request: [closed]`
- Also supports `workflow_dispatch` for manual cleanup
- Drops: DCM project, ephemeral database, and all ephemeral roles
- Discovers roles dynamically: `SHOW ROLES LIKE '%_PR{N}%'`

### Step 7: Verify Snowflake Grants

Validate the CI role has all required privileges:
```sql
SHOW GRANTS TO ROLE <ci_role>;
```

Required grants:
- `CREATE DATABASE ON ACCOUNT`
- `CREATE ROLE ON ACCOUNT`
- `MANAGE GRANTS ON ACCOUNT`
- `USAGE ON WAREHOUSE <wh>`
- `OPERATE ON WAREHOUSE <wh>`
- `USAGE ON INTEGRATION <eai>` (if applicable)

### Step 8: Test End-to-End

1. Open a PR that modifies files in the DCM project path
2. Verify the deploy workflow runs successfully
3. Check Snowflake for the ephemeral database and DCM project
4. Close/merge the PR
5. Verify the teardown workflow cleans up all objects

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `Schema 'X.DCM' does not exist` | Clone preserves ACCOUNTADMIN ownership | Add ownership transfer grants after clone |
| `alias already exists` | Same deploy alias reused across runs | Use `pr-{N}-run{RUN}-{SHA}` format |
| `Insufficient privileges on integration` | CI role lacks USAGE on EAI | `GRANT USAGE ON INTEGRATION ... TO ROLE ...` |
| `project_name` not resolving | Jinja2 not supported in `project_name` | Use sed placeholder `___PR_NUMBER___` |
| Hidden deploy errors | Output captured in variable hides errors | Use `tee` + `${PIPESTATUS[0]}` pattern |
| plan.json queries fail | Wrong jq schema assumed | Schema is `.changeset[].type` + `.changeset[].object_id.domain` |

## Terraform Integration

If managing Snowflake infrastructure with Terraform, add EAI resources:

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
