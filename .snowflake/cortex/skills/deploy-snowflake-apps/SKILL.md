---
name: deploy-snowflake-apps
description: "Deploy Streamlit apps and Notebooks to Snowflake via snow CLI. Also generates GitHub Actions workflows for CI/CD automation."
tools:
  - Bash
  - Read
  - Write
  - ask_user_question
---

# Deploy Snowflake Apps

Automates deployment of Streamlit in Snowflake (SiS) apps and Snowflake Notebooks using `snow` CLI.
Also generates GitHub Actions CI/CD workflows for automated deployment on push.

## When to Use

- User wants to deploy a Streamlit app to Snowflake (`snow streamlit deploy`)
- User wants to deploy a Notebook to Snowflake (`snow notebook deploy`)
- User wants to generate GitHub Actions workflows for automated deployment
- User asks about CI/CD for Streamlit or Notebook projects in this repo

## Key Facts

- **DCM does NOT support Streamlit or Notebook objects.** These must be deployed via `snow streamlit deploy` / `snow notebook deploy` using `snowflake.yml` project definitions.
- Streamlit apps live in `streamlit-apps/<app_name>/` with a `snowflake.yml` each.
- Notebooks live in `notebooks/<notebook_name>/` with a `snowflake.yml` each.
- The `--connection` flag specifies which Snowflake connection to use (from `~/.snowflake/connections.toml`).
- Use `--replace` to update existing apps/notebooks.

## Directory Convention

```
streamlit-apps/
  <app_name>/
    snowflake.yml          # snow CLI project definition
    streamlit_app.py       # entrypoint
    environment.yml        # conda deps for SiS
    views/                 # pages (NOT pages/ — conflicts with legacy auto-discovery)
    shared/                # reusable modules
notebooks/
  <notebook_name>/
    snowflake.yml          # snow CLI project definition
    notebook.ipynb         # the notebook
```

## Deployment Commands

### Deploy a Streamlit app

```bash
snow streamlit deploy \
  --project streamlit-apps/<app_name> \
  --replace \
  --connection <connection_name>
```

### Deploy a Notebook

**NOTE:** `snow notebook deploy --project <path>` may fail with absolute paths. Use `cd` instead:

```bash
cd notebooks/<notebook_name> && \
  snow notebook deploy --replace --connection <connection_name>
```

### Deploy ALL apps and notebooks

```bash
# Deploy all Streamlit apps
for app in streamlit-apps/*/; do
  echo "Deploying Streamlit: $app"
  snow streamlit deploy --project "$app" --replace --connection <connection_name>
done

# Deploy all Notebooks
for nb in notebooks/*/; do
  if [ -f "$nb/snowflake.yml" ]; then
    echo "Deploying Notebook: $nb"
    (cd "$nb" && snow notebook deploy --replace --connection <connection_name>)
  fi
done
```

## Workflow: Interactive Deployment

When the user asks to deploy:

1. **Detect apps**: List all `streamlit-apps/*/snowflake.yml` and `notebooks/*/snowflake.yml`.
2. **Ask what to deploy**: Present checkboxes for each discovered app/notebook.
3. **Ask for connection**: Which Snow CLI connection to use (check `config.example.yml` for hints).
4. **Run deployment**: Execute `snow streamlit deploy` / `snow notebook deploy` for each selected item.
5. **Report results**: Show success/failure and Snowflake URLs for each.

## Workflow: Generate GitHub Actions

When the user asks for CI/CD:

1. Generate `.github/workflows/deploy-apps.yml` using the template below.
2. The workflow should:
   - Trigger on push to `main` when files in `streamlit-apps/` or `notebooks/` change
   - Install `snowflake-cli`
   - Use a Snowflake service connection (key-pair auth) stored as GitHub secrets
   - Deploy changed apps/notebooks via `snow streamlit deploy` / `snow notebook deploy`

### GitHub Actions Template

```yaml
name: Deploy Snowflake Apps

on:
  push:
    branches: [main]
    paths:
      - 'streamlit-apps/**'
      - 'notebooks/**'
  workflow_dispatch:

env:
  SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
  SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
  SNOWFLAKE_PRIVATE_KEY_RAW: ${{ secrets.SNOWFLAKE_PRIVATE_KEY }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Snowflake CLI
        run: pip install snowflake-cli

      - name: Write connection config
        run: |
          mkdir -p ~/.snowflake
          cat > ~/.snowflake/connections.toml << EOF
          [deploy]
          account = "$SNOWFLAKE_ACCOUNT"
          user = "$SNOWFLAKE_USER"
          authenticator = "SNOWFLAKE_JWT"
          private_key_file = "/tmp/snowflake_key.p8"
          warehouse = "SWISSFLAKES_WH_ADMIN"
          role = "SWISSFLAKES_PLATFORM_ADMIN"
          EOF
          echo "$SNOWFLAKE_PRIVATE_KEY_RAW" > /tmp/snowflake_key.p8
          chmod 600 /tmp/snowflake_key.p8

      - name: Deploy Streamlit apps
        run: |
          for app in streamlit-apps/*/; do
            if [ -f "$app/snowflake.yml" ]; then
              echo "::group::Deploying $app"
              snow streamlit deploy --project "$app" --replace --connection deploy
              echo "::endgroup::"
            fi
          done

      - name: Deploy Notebooks
        run: |
          for nb in notebooks/*/; do
            if [ -f "$nb/snowflake.yml" ]; then
              echo "::group::Deploying $nb"
              (cd "$nb" && snow notebook deploy --replace --connection deploy)
              echo "::endgroup::"
            fi
          done
```

## snowflake.yml Reference

### Streamlit

```yaml
definition_version: 2
entities:
  <entity_id>:
    type: streamlit
    identifier:
      name: MY_STREAMLIT_APP
      schema: MY_SCHEMA
      database: MY_DATABASE
    query_warehouse: MY_WAREHOUSE
    main_file: streamlit_app.py
    title: "Human-readable title"
    comment: "Description"
    artifacts:
      - streamlit_app.py
      - environment.yml
      - views/home.py
      - shared/data.py
```

### Notebook

```yaml
definition_version: 2
entities:
  <entity_id>:
    type: notebook
    identifier:
      name: MY_NOTEBOOK
      schema: MY_SCHEMA
      database: MY_DATABASE
    query_warehouse: MY_WAREHOUSE
    notebook_file: notebook.ipynb
    artifacts:
      - notebook.ipynb
```

## CRITICAL: Streamlit Multi-Page Pattern

- Use `views/` directory, NEVER `pages/` (conflicts with Streamlit legacy auto-discovery in SiS)
- Use `st.navigation()` + `st.Page("views/xxx.py")` pattern
- Do NOT set `pages_dir` in snowflake.yml; list view files in `artifacts` instead
- See the `streamlit-multipage-nav` skill for detailed patterns

## Current Inventory

| Type | Name | Location | Target DB.SCHEMA |
|------|------|----------|------------------|
| Streamlit | SFG_ENTERPRISE_DASHBOARD | streamlit-apps/sfg_enterprise/ | SFG_ENTERPRISE.MART_FULFILLMENT |
| Streamlit | SFG_ADMIN_DASHBOARD | streamlit-apps/sfg_admin/ | SFG_ADMIN.GOVERNANCE |
| Notebook | SFG_ENTERPRISE_EXPLORATION | notebooks/sfg_enterprise_exploration/ | SFG_ENTERPRISE.MART_FULFILLMENT |
| Notebook | COMPLIANCE_ANALYSIS | notebooks/compliance_analysis/ | SFG_ENTERPRISE.MART_COMPLIANCE |
