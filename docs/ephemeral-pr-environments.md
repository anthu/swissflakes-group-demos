# Ephemeral PR Environments with DCM + GitHub Actions

Automatically create isolated Snowflake test environments when a PR is opened and tear them down when the PR is closed or merged.

## How It Works

```
PR opened/updated                         PR closed/merged
       │                                         │
       ▼                                         ▼
┌──────────────────────┐                ┌─────────────────────┐
│  Deploy Workflow      │                │  Teardown Workflow   │
│                       │                │                      │
│  1. PARSE_MANIFEST    │                │  1. Drop DCM project │
│  2. Clone source DB   │                │  2. Drop ephemeral DB│
│  3. Transfer ownership│                │  3. Drop all PR roles│
│  4. DCM plan          │                │  4. Comment on PR    │
│  5. Drop detection    │                │                      │
│  6. DCM deploy        │                └─────────────────────┘
│  7. Refresh DTs       │
│  8. Test expectations │
│  9. Comment on PR     │
└──────────────────────┘
```

Each PR gets:
- A zero-copy clone of the source database: `{SOURCE_DB}_PR{N}`
- A DCM project deployed into that clone with all schema changes from the PR
- Dynamic tables refreshed and data quality tests run
- A summary comment posted to the PR with job results

## Files

| File | Purpose |
|------|---------|
| `.github/workflows/dcm_pr_ephemeral_deploy.yml` | Deploy workflow (7 jobs) |
| `.github/workflows/dcm_pr_ephemeral_teardown.yml` | Teardown workflow (2 jobs) |
| `.github/requirements-snowcli.txt` | Pip requirements for Snow CLI |
| `data_products/*/manifest.yml` | DCM manifest with `PR_EPHEMERAL` target |
| `infrastructure/terraform/github_eai.tf` | EAI for GitHub dbt package downloads |

## Prerequisites

### Snowflake

| Requirement | Details |
|-------------|---------|
| Service user | `TYPE=SERVICE` with a programmatic access token (PAT) |
| CI role | Account-level: `CREATE DATABASE`, `CREATE ROLE`, `MANAGE GRANTS` |
| Warehouse | `USAGE` + `OPERATE` granted to CI role |
| EAI (if using dbt GitHub packages) | `USAGE ON INTEGRATION` granted to CI role |
| Source DB ownership | All objects owned by a role the CI role can impersonate (NOT `ACCOUNTADMIN`) |
| Network policy | Allow GitHub Actions IPs via `SNOWFLAKE.NETWORK_SECURITY.GITHUBACTIONS_GLOBAL` |

### GitHub

| Type | Name | Value |
|------|------|-------|
| Secret | `DEPLOYER_PAT` | Snowflake programmatic access token |
| Variable | `SNOWFLAKE_USER` | Service user name |
| Variable | `SNOWFLAKE_ACCOUNT` | Account identifier |
| Variable | `SNOWFLAKE_CI_ROLE` | CI role name |
| Variable | `SNOWFLAKE_WAREHOUSE` | Warehouse name |

## Adding Ephemeral PR Support to a DCM Project

### 1. Add PR_EPHEMERAL Target to manifest.yml

The `project_name` field does NOT support Jinja2 templating. Use a sed placeholder instead:

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

The `___PR_NUMBER___` placeholder is resolved at runtime by:
```bash
sed -i "s/___PR_NUMBER___/${PR_NUMBER}/g" manifest.yml
```

### 2. Ensure Source DB Ownership

All objects must be owned by a role other than `ACCOUNTADMIN`. Clone preserves ownership, and the CI role cannot access `ACCOUNTADMIN`-owned objects.

```sql
-- Check for ACCOUNTADMIN-owned objects
SELECT table_schema, table_name, table_owner
FROM <SOURCE_DB>.information_schema.tables
WHERE table_owner = 'ACCOUNTADMIN';

-- Transfer ownership (run for each object type)
GRANT OWNERSHIP ON DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL TABLES IN DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL VIEWS IN DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL DYNAMIC TABLES IN DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL STAGES IN DATABASE <SOURCE_DB> TO ROLE <owner_role> COPY CURRENT GRANTS;
```

### 3. Create the Deploy Workflow

Create `.github/workflows/dcm_pr_ephemeral_deploy.yml` with these jobs:

**PARSE_MANIFEST** — Reads the manifest and outputs account, role, project_name.

**PLAN** — Clones the source DB, transfers ownership to the CI role, creates the DCM project, and runs `snow dcm plan --save-output`. Parses `out/plan.json` to produce a summary of CREATE/ALTER/DROP operations.

**DROP_DETECTION** — Safety gate that fails the pipeline if the plan contains DROP operations on critical object types (DATABASE, SCHEMA, TABLE, STAGE).

**DEPLOY** — Runs `snow dcm deploy` with a unique alias: `pr-{PR}-run{RUN}-{SHA}`. Uses `tee` + `${PIPESTATUS[0]}` to capture output while preserving the exit code.

**REFRESH_DYNAMIC_TABLES** — Runs `snow dcm refresh` to trigger dynamic table refreshes.

**TEST_EXPECTATIONS** — Runs `snow dcm test` to validate data quality expectations.

**COMMENT_ON_PR** — Posts a summary table to the PR with pass/fail status for each job.

### 4. Create the Teardown Workflow

Create `.github/workflows/dcm_pr_ephemeral_teardown.yml` triggered on `pull_request: [closed]`:

- Drops the DCM project: `snow dcm drop --target PR_EPHEMERAL`
- Drops the ephemeral database: `DROP DATABASE IF EXISTS {SOURCE_DB}_PR{N}`
- Discovers and drops all ephemeral roles: `SHOW ROLES LIKE '%_PR{N}%'`
- Supports `workflow_dispatch` for manual cleanup of orphaned environments

### 5. Manage EAI in Terraform (if applicable)

If DCM definition files reference dbt packages from GitHub, an External Access Integration is required:

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

## Key Technical Details

### plan.json Schema

`snow dcm plan --save-output` produces `out/plan.json`:

```json
{
  "changeset": [
    {
      "type": "CREATE",
      "object_id": {
        "domain": "TABLE",
        "name": "MY_TABLE",
        "fqn": "DB.SCHEMA.MY_TABLE"
      },
      "changes": [...]
    }
  ],
  "metadata": {...},
  "version": "..."
}
```

Operation types: `CREATE`, `ALTER`, `DROP`
Object domains: `ROLE`, `DATABASE`, `SCHEMA`, `TABLE`, `VIEW`, `DYNAMIC_TABLE`, `STAGE`, `TASK`, `PROCEDURE`, etc.

### Deploy Alias Uniqueness

Each deploy must have a unique alias. Using `pr-{PR_NUMBER}` alone causes "alias already exists" errors on re-runs. Include the run number and git SHA:

```bash
SHORT_SHA=$(echo "${{ github.sha }}" | cut -c1-7)
snow dcm deploy --target PR_EPHEMERAL --alias "pr-${{ env.PR_NUMBER }}-run${{ github.run_number }}-${SHORT_SHA}" -x
```

### Output Capture with Exit Code Preservation

Capturing command output in a variable hides errors from the GitHub Actions log. Use `tee` instead:

```bash
set +e
snow dcm deploy ... 2>&1 | tee /tmp/deploy_output.txt
EXIT_CODE=${PIPESTATUS[0]}
set -e
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Schema 'X.DCM' does not exist` | Clone preserves ACCOUNTADMIN ownership | Add ownership transfer grants after clone |
| `alias already exists` | Same alias reused across runs | Use `pr-{N}-run{RUN}-{SHA}` format |
| `Insufficient privileges on integration` | CI role lacks USAGE on EAI | `GRANT USAGE ON INTEGRATION ... TO ROLE ...` |
| `project_name` not resolving | Jinja2 not supported in `project_name` | Use sed placeholder `___PR_NUMBER___` |
| Deploy errors hidden in logs | Output captured in variable | Use `tee` + `${PIPESTATUS[0]}` pattern |
| plan.json jq queries fail | Wrong schema assumed | Use `.changeset[].type` + `.changeset[].object_id.domain` |
| Tables inaccessible after clone | Source objects owned by ACCOUNTADMIN | Transfer ownership to DP owner role before cloning |
