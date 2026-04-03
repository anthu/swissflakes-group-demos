# Teardown Workflow Template

Complete GitHub Actions workflow for cleaning up DCM ephemeral environments when a PR is closed or merged.

## File: `.github/workflows/dcm_pr_ephemeral_teardown.yml`

```yaml
name: DCM PR Ephemeral Teardown

on:
  pull_request:
    types: [closed]
    branches: ["main"]
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to tear down (for manual cleanup)'
        required: true
        type: string

env:
  DCM_PROJECT_PATH: <DCM_PROJECT_PATH>/
  SNOWFLAKE_PASSWORD: ${{ secrets.DEPLOYER_PAT }}
  SNOWFLAKE_USER: ${{ vars.SNOWFLAKE_USER }}
  SNOWFLAKE_ACCOUNT: ${{ vars.SNOWFLAKE_ACCOUNT }}
  SNOWFLAKE_CI_ROLE: ${{ vars.SNOWFLAKE_CI_ROLE }}
  PR_NUMBER: ${{ github.event.pull_request.number || github.event.inputs.pr_number }}
  SNOWFLAKE_WAREHOUSE: ${{ vars.SNOWFLAKE_WAREHOUSE }}

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  TEARDOWN:
    runs-on: ubuntu-latest
    env:
      SNOWFLAKE_ROLE: ${{ vars.SNOWFLAKE_CI_ROLE }}
    steps:
    - name: Clone Repo
      uses: actions/checkout@v4
    - name: Resolve PR number in manifest
      run: sed -i "s/___PR_NUMBER___/${{ env.PR_NUMBER }}/g" ${{ env.DCM_PROJECT_PATH }}manifest.yml
    - name: Setup Python + SnowCLI
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
        cache-dependency-path: .github/requirements-snowcli.txt
    - run: pip install -r .github/requirements-snowcli.txt
    - name: Drop DCM project
      run: |
        cd ./$DCM_PROJECT_PATH
        snow dcm drop --target PR_EPHEMERAL -x 2>&1 || true
    - name: Drop ephemeral database
      run: |
        # --- REPLACE <SOURCE_DB> with your actual source database name ---
        DB_NAME="<SOURCE_DB>_PR${{ env.PR_NUMBER }}"
        snow sql -q "DROP DATABASE IF EXISTS ${DB_NAME}" -x
        echo "### Dropped database ${DB_NAME}" >> $GITHUB_STEP_SUMMARY
    - name: Drop ephemeral roles
      run: |
        # Discover and drop all roles created for this PR
        ROLES=$(snow sql -q "SHOW ROLES LIKE '%_PR${{ env.PR_NUMBER }}%'" -x --format json 2>/dev/null | jq -r '.[].name' 2>/dev/null || echo "")
        if [ -z "$ROLES" ]; then
          echo "No ephemeral roles found for PR #${{ env.PR_NUMBER }}" >> $GITHUB_STEP_SUMMARY
        else
          echo "### Dropping ephemeral roles:" >> $GITHUB_STEP_SUMMARY
          echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
          while IFS= read -r ROLE; do
            if [ -n "$ROLE" ]; then
              snow sql -q "DROP ROLE IF EXISTS \"${ROLE}\"" -x 2>&1 || true
              echo "- Dropped: ${ROLE}" >> $GITHUB_STEP_SUMMARY
            fi
          done <<< "$ROLES"
          echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
        fi

  COMMENT_ON_PR:
    needs: TEARDOWN
    if: always() && github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: write
    steps:
      - name: Post cleanup confirmation
        uses: actions/github-script@v7
        env:
          TEARDOWN_RESULT: ${{ needs.TEARDOWN.result }}
        with:
          script: |
            const result = process.env.TEARDOWN_RESULT;
            const emoji = result === 'success' ? 'PASS' : 'FAIL';
            const runUrl = `https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
            const prState = context.payload.pull_request.merged ? 'merged' : 'closed';
            let comment = `### DCM Ephemeral Environment Teardown - PR #${context.issue.number}\n\n`;
            comment += `PR was **${prState}**. Ephemeral environment cleanup: **${emoji} ${result}**\n\n`;
            comment += `[View teardown workflow run](${runUrl})`;
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## Customization Points

Replace these placeholders before committing:
- `<DCM_PROJECT_PATH>` — relative path to DCM project (e.g., `data_products/sfg_logistics`)
- `<SOURCE_DB>` — production database name (e.g., `SFG_LOGISTICS`)

## Manual Cleanup

Use `workflow_dispatch` to manually tear down orphaned environments:
1. Go to Actions > DCM PR Ephemeral Teardown
2. Click "Run workflow"
3. Enter the PR number to clean up
