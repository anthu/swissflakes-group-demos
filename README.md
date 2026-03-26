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

- **Data Mesh** -- 1 DB per data product, Internal Marketplace listings (declarative sharing)
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
   T2  Platform DCM        data_products/platform/
   T3  Source DP DCM (x8)  data_products/{name}/dcm/
   T4  dbt seeds           EXECUTE DBT PROJECT ... ARGS = 'seed'
   T5  Terraform           infrastructure/terraform/
   T6  Listings            listings/
   T7  Enterprise DPs      data_products/{fulfillment,customer_360,revenue_analytics,compliance}/
   T8  Cortex Agent        cortex-agent/ + semantic-views/
   T9  Openflow            openflow/
   T10 Docs                docs/
   ```

## Repo Structure

```
swissflakes-group-demos/
├── config.example.yml          # Connection config template
├── data_products/              # One folder per data product
│   ├── platform/               # SWISSFLAKES_ADMIN (DCM)
│   ├── shipments/              # dcm/ (includes embedded dbt)
│   ├── fleet/
│   ├── locations/
│   ├── orders/
│   ├── customers/
│   ├── products/
│   ├── transactions/
│   ├── merchants/
│   ├── fulfillment/
│   ├── customer_360/
│   ├── revenue_analytics/
│   └── compliance/
├── listings/                   # Internal Marketplace configs
├── infrastructure/terraform/   # Security policies, monitors
├── openflow/                   # Live feed connector configs
├── cortex-agent/               # Cortex Agent definition
├── semantic-views/             # Semantic view SQL DDL files
└── docs/                       # Workshop guides
```

## Regulations Covered

| Regulation | Domain |
|-----------|--------|
| BAZG | Customs declarations (Passar) |
| FINMA | Payment processing |
| DSG / nFADP | Swiss data protection |
| PCI-DSS | Card data security |
| GwG | Anti-money laundering |
