# DCM Manifest PR_EPHEMERAL Target Configuration

## Placeholder Pattern

DCM `project_name` does NOT support Jinja2 templating. Use a sed placeholder instead:

```yaml
# manifest.yml
targets:
  # Production target
  PROD:
    account_identifier: '<account>'
    project_name: '<SOURCE_DB>'
    project_owner: '<prod_owner_role>'

  # Ephemeral PR target — ___PR_NUMBER___ is replaced by sed in CI
  PR_EPHEMERAL:
    account_identifier: '<account>'
    project_name: '<SOURCE_DB>_PR___PR_NUMBER___'
    project_owner: '<ci_role>'
    templating_config:
      variables:
        env: 'PR___PR_NUMBER___'
```

## How the Placeholder is Resolved

In every GitHub Actions job that reads the manifest:

```bash
sed -i "s/___PR_NUMBER___/${{ env.PR_NUMBER }}/g" manifest.yml
```

This transforms:
- `project_name: SFG_LOGISTICS_PR___PR_NUMBER___` → `project_name: SFG_LOGISTICS_PR42`
- `env: PR___PR_NUMBER___` → `env: PR42`

## Important Notes

1. The sed replacement must happen in EVERY job that reads the manifest (each job gets a fresh checkout)
2. The placeholder pattern `___` (triple underscore) is chosen to avoid conflicts with normal content
3. The `templating_config.variables.env` variable can be used in DCM definition files via Jinja2: `{{ env }}`
4. Each PR gets a unique DCM project: `<SOURCE_DB>_PR{N}.DCM.DP_<SOURCE_DB>_PR{N}`
