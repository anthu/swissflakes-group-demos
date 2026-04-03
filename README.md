# SwissFlakes Group Demos

End-to-end Snowflake demo for **SwissFlakes Group**, a fictional Swiss holding company with two subsidiaries:

- **SwissFlakes Logistics AG** (Basel) -- B2B freight, fulfillment, order management
- **SwissFlakes Pay AG** (Zurich) -- Payment processing

## What's Inside

| Layer | Data Products |
|-------|--------------|
| Source (Logistics AG) | SHIPMENTS, FLEET, LOCATIONS, ORDERS, CUSTOMERS, PRODUCTS, **OPEN_TRANSPORT** |
| Source (Pay AG) | TRANSACTIONS, MERCHANTS |
| Enterprise | FULFILLMENT, CUSTOMER_360, **WEATHER** |
| Consumer | REVENUE_ANALYTICS, COMPLIANCE |
| Platform | SWISSFLAKES_ADMIN |

### Features Demonstrated

- **Data Mesh** -- 1 DB per domain, per-sub-DP Internal Marketplace listings via `dbt-snowflake-listings`
- **DCM** -- Database Change Management for all infrastructure
- **dbt** -- Seed data, staging, and marts models
- **Governance** -- Masking policies, RLS, DATA_QUALITY tags (BRONZE/SILVER/GOLD)
- **Cortex** -- Semantic views + Cortex Agent for natural language analytics
- **Openflow** -- Live feeds from Swiss open data APIs (transport, weather, SBB, ECB)
- **Openflow dbt** -- LATERAL FLATTEN transforms on streamed VARIANT data into analytics marts
- **Terraform** -- Security infrastructure (policies, monitors, network rules)

## Prerequisites

- Snowflake account(s) with ACCOUNTADMIN
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli) (`snow`) installed
- Terraform (optional, for security infrastructure)

## Setup

1. Copy and fill in the config:
   ```bash
   cp config.example.yml config.yml
   # Edit config.yml with your Snow CLI connection names
   ```

2. Deploy in order:
   ```
   T1  Scaffold            (this repo)
   T2  Platform DCM        data_products/sfg_admin/
   T3  Source Domain DCM   data_products/sfg_logistics/ + data_products/sfg_pay/
   T4  dbt seed + run      EXECUTE DBT PROJECT ... ARGS = 'seed' then 'run'
   T5  Terraform           infrastructure/terraform/
   T6  Enterprise DPs      data_products/sfg_enterprise/
   T7  Cortex Agent        cortex-agent/
   T8  Openflow            openflow/
   T9  Docs                docs/
   ```
   Listings are created automatically during `dbt run` (step T4) via the `organization_listing` materialization.

## Repo Structure

```
swissflakes-group-demos/
├── config.example.yml          # Connection config template
├── data_products/              # DCM projects (one per domain)
│   ├── sfg_admin/              # Platform: roles, tags, governance
│   ├── sfg_logistics/          # 7 sub-DPs with embedded dbt + listings
│   ├── sfg_pay/                # 2 sub-DPs with embedded dbt + listings
│   └── sfg_enterprise/         # Consumer DPs (fulfillment, customer_360, etc.)
├── infrastructure/terraform/   # Security policies, EAI, monitors
├── openflow/                   # Live feed connector scripts
├── cortex-agent/               # Cortex Agent spec + creation SQL
├── streamlit-apps/             # Streamlit in Snowflake apps
├── notebooks/                  # Snowflake Notebooks
└── docs/                       # Workshop guides
```

## CI/CD: Ephemeral PR Environments

When a pull request is opened against `main` that touches `data_products/sfg_logistics/**`, GitHub Actions automatically:

1. **Creates** an isolated Snowflake environment (`SFG_LOGISTICS_PR<number>`) via DCM
2. **Deploys** all schemas, tables, roles, and grants into it
3. **Tests** data quality expectations
4. **Posts** a summary (CREATE/ALTER/DROP counts + test results) as a PR comment
5. **Tears down** the entire environment when the PR is closed or merged

### GitHub Setup

| Name | Type | Description |
|------|------|-------------|
| `DEPLOYER_PAT` | Secret | Snowflake service user password |
| `SNOWFLAKE_USER` | Variable | Service user name (e.g. `GITHUB_ACTIONS_SVC`) |
| `SNOWFLAKE_ACCOUNT` | Variable | Snowflake account identifier |
| `SNOWFLAKE_CI_ROLE` | Variable | Role with CREATE DATABASE + CREATE ROLE privileges |

### Snowflake Pre-requisites

- A service user whose role (set via `SNOWFLAKE_CI_ROLE`) has `CREATE DATABASE` and `CREATE ROLE` on the account
- The role must be able to grant roles to itself (for the ephemeral owner role hierarchy)

### Manual Teardown

If a teardown fails or you need to clean up manually, use `workflow_dispatch` on the teardown workflow and provide the PR number.

## Regulations Covered

| Regulation | Domain |
|-----------|--------|
| BAZG | Customs declarations (Passar) |
| FINMA | Payment processing |
| DSG / nFADP | Swiss data protection |
| PCI-DSS | Card data security |
| GwG | Anti-money laundering |
