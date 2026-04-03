# AGENTS.md -- SwissFlakes Group Demos

Quick reference for sub-agents working on this repo.

## Config

- `config.example.yml` -- template (committed)
- `config.yml` -- actual values (gitignored)
- NEVER hardcode account names, usernames, or connection names in code

## Connections

Use `--connection` from config.yml. Two accounts:
- `prod_connection` -- primary demo environment
- `dev_connection` -- CI/CD, cross-account sharing

## Database Layout

4 domain databases. Each has schemas: RAW_<source> / STG_<dp> / MART_<dp>.

Quality encoded via tag `DATA_QUALITY` (BRONZE / SILVER / GOLD), not schema names.

| Database | Subsidiary | Data Products (schemas) |
|---|---|---|
| SFG_LOGISTICS | Logistics AG | customers, shipments, fleet, locations, orders, products, **open_transport** |
| SFG_PAY | Pay AG | transactions, merchants |
| SFG_ENTERPRISE | Group | fulfillment, customer_360, revenue_analytics, compliance, **weather** |
| SFG_ADMIN | Group | governance, agents (platform) |

## RBAC Pattern

Per data product:
- `DP_{NAME}_OWNER` -- full DB control
- `DP_{NAME}_WRITER` -- RAW + STAGING read/write
- `DP_{NAME}_READER` -- MARTS read-only

Platform roles: `SWISSFLAKES_PLATFORM_ADMIN`, `SWISSFLAKES_DATA_ENGINEER`, `SWISSFLAKES_DATA_ANALYST`, `SWISSFLAKES_COMPLIANCE_OFFICER`, `SWISSFLAKES_CORTEX_ANALYST`, `SWISSFLAKES_BI_CONSUMER`

Publisher roles (per subsidiary, defined in `data_products/sfg_admin/sources/definitions/02_access.sql`):
- `SFG_LOGISTICS_DATA_PUBLISHER` -- `CREATE SHARE`, `CREATE ORGANIZATION LISTING`, `IMPORT SHARE` on account
- `SFG_PAY_DATA_PUBLISHER` -- same privileges

Each publisher role is granted to the respective domain owner (`DP_SFG_LOGISTICS_OWNER`, `DP_SFG_PAY_OWNER`) in their `01_infrastructure.sql`.

## Internal Marketplace (Per-Sub-DP Listings)

Each sub-DP publishes its own organization listing using the [`dbt-snowflake-listings`](https://github.com/anthu/dbt-snowflake-listings) package (v0.2.3).
Listings are embedded directly in each dbt project -- no separate listing project needed.

| Listing | Share | Producer | MART Table |
|---------|-------|----------|------------|
| SFG_LOGISTICS_CUSTOMERS | SFG_LOGISTICS_CUSTOMERS | SFG_LOGISTICS | MART_CUSTOMERS.MART_CUSTOMER_OVERVIEW |
| SFG_LOGISTICS_SHIPMENTS | SFG_LOGISTICS_SHIPMENTS | SFG_LOGISTICS | MART_SHIPMENTS.MART_SHIPMENT_TRACKING |
| SFG_LOGISTICS_FLEET | SFG_LOGISTICS_FLEET | SFG_LOGISTICS | MART_FLEET.MART_FLEET_STATUS |
| SFG_LOGISTICS_LOCATIONS | SFG_LOGISTICS_LOCATIONS | SFG_LOGISTICS | MART_LOCATIONS.MART_WAREHOUSE_CAPACITY |
| SFG_LOGISTICS_ORDERS | SFG_LOGISTICS_ORDERS | SFG_LOGISTICS | MART_ORDERS.MART_ORDER_SUMMARY |
| SFG_LOGISTICS_PRODUCTS | SFG_LOGISTICS_PRODUCTS | SFG_LOGISTICS | MART_PRODUCTS.MART_PRODUCT_CATALOG |
| SFG_LOGISTICS_OPEN_TRANSPORT | SFG_LOGISTICS_OPEN_TRANSPORT | SFG_LOGISTICS | MART_OPEN_TRANSPORT.MART_SWISS_RAIL_OVERVIEW |
| SFG_PAY_TRANSACTIONS | SFG_PAY_TRANSACTIONS | SFG_PAY | MART_TRANSACTIONS.MART_TRANSACTION_SUMMARY |
| SFG_PAY_MERCHANTS | SFG_PAY_MERCHANTS | SFG_PAY | MART_MERCHANTS.MART_MERCHANT_OVERVIEW |

**Pattern (per dbt project):**
- `packages.yml` -- references `dbt-snowflake-listings` v0.2.3 via git
- `models/listings/{listing_name}.sql` -- `{{ dbt_snowflake_listings.share_model(ref('mart_...')) }}`
- `models/listings/schema.yml` -- `organization_listing` materialization config + manifest YAML
- DCM definition (`02_dbt_*.sql`) includes `EXTERNAL_ACCESS_INTEGRATIONS = (SWISSFLAKES_GITHUB_EAI)` for `dbt deps`
- **Access scope:** Every listing manifest sets `organization_targets.discovery` and `organization_targets.access` to `all_internal_accounts: true` so the whole org can discover and consume (subject to roles in the consumer account).
- **Publish state:** Every listing keeps `publish: false` so it stays **unpublished** (DRAFT in the UI). Set `publish: true` only when you intentionally publish (requires organization profile where applicable).

**Listing titles:** Prefix with **⚜️** so listings are easy to spot in the Internal Marketplace UI.

**Manifest contacts (listing support / approver):**
- Logistics listings: `anton.huck+lgs@snowflake.com` (both `support_contact` and `approver_contact`)
- Pay listings: `anton.huck+pay@snowflake.com`

These addresses appear only in listing manifests (explicit exception to avoiding personal identifiers in repo).

**Documentation link:** Manifests use Snowflake’s [listing manifest reference](https://docs.snowflake.com/en/progaccess/listing-manifest-reference) as `resources.documentation` until a product-specific public URL exists.

**Data preview vs Marketplace listings:** Public Marketplace listings (e.g. KuCoin-style products) are configured in Provider Studio, where “Save and Create Data Dictionary” drives previews and refresh behavior ([provider listings reference](https://docs.snowflake.com/en/collaboration/provider-listings-reference)). **Organizational** listings use the same manifest family: include optional `data_preview` (`has_pii: false` unless you have a safe pattern) alongside `data_dictionary.featured` so consumers can enable **Data preview** in the listing UI. **`EXECUTE DBT PROJECT` uses the dbt sources last uploaded by `snow dcm deploy`** for that DCM project; local edits to `sources/dbt_*` are invisible until you redeploy the parent `data_products/{name}` bundle. **Package caveat (`dbt-snowflake-listings` v0.2.3):** `metadata_overrides.objects[].pii_columns` is serialized twice in `_serialize_manifest` (duplicate YAML key); avoid `pii_columns` lists in manifest until the package fixes that macro. Snowflake can still classify and mask preview columns separately ([provider reference](https://docs.snowflake.com/en/collaboration/provider-listings-reference)).

**Column descriptions in the listing UI** come from **Snowflake column COMMENTs** on the shared table, not from dbt `schema.yml` alone. Each sub-DP sets `+persist_docs: { relation: true, columns: true }` on **marts** in `dbt_project.yml` so `models/marts/schema.yml` descriptions are written to the warehouse when marts run. Re-run `dbt run` (or `--full-refresh` on the mart if needed) after changing descriptions.

**Note:** `models/listings/schema.yml` must be plain YAML (no Jinja in `listing_manifest`); Snowflake DCM / `deps_compile` validates it before dbt renders Jinja.

**EAI:** `SWISSFLAKES_GITHUB_EAI` allows egress to `github.com` + `codeload.github.com` for dbt package downloads.

## DCM Convention

- DCM projects live in `data_products/{name}/` (flat, no dcm/ subfolder)
- Jinja templating with `{{env_suffix}}`, `{{dp_name}}`, `{{dp_type}}` from manifest.yml
- DEV/PROD targets: `{{env_suffix}}` = `_DEV` or `""`
- Commands: `snow dcm create {FQN} --if-not-exists -c <connection>`, `snow dcm deploy --from data_products/{name} -c <connection>`
- Projects: `{DB}.DCM.DP_{DB}` (infrastructure) + `{DB}.DCM.DBT_{DP}` (dbt per sub-DP)
- Platform: `SFG_ADMIN.DCM.PLATFORM`
- **DCM does NOT support DEFINE STREAMLIT or DEFINE NOTEBOOK** — use `snow streamlit deploy` / `snow notebook deploy` instead

## dbt Convention

- dbt projects are embedded in DCM via `DEFINE DBT PROJECT` in `data_products/{name}/sources/definitions/02_dbt*.sql`
- dbt source lives in `data_products/{name}/sources/dbt_{dp}/`
- Source DPs: seeds in `seeds/`, staging in `models/staging/`, marts in `models/marts/`
- Enterprise/Consumer DPs: no seeds, cross-DB `source()` references in `models/marts/schema.yml`
- Custom `generate_schema_name` macro required so dbt uses exact schema names
- **Important:** `generate_schema_name` must use `{%- set default_schema = target.schema -%}`, NOT bare `{{ default_schema }}` (empty during Snowflake `deps_compile`)
- Execute via: `EXECUTE DBT PROJECT {DB}.DCM.DBT_{DB} ARGS = 'run'`
- Profile name = lowercase DB name, no `env_var()` or `password` (Snowflake session handles auth)

### Openflow dbt Projects (source() + LATERAL FLATTEN)

Two dbt projects transform Openflow raw data (single VARIANT column `RAW`) into analytics-ready marts:

| dbt Project | DCM Object | Source Tables | Mart Table | Rows |
|-------------|-----------|---------------|------------|------|
| `dbt_open_transport` | `SFG_LOGISTICS.DCM.DBT_OPEN_TRANSPORT` | `RAW_LOCATIONS.TRANSPORT_CONNECTIONS`, `RAW_SHIPMENTS.SBB_STATIONBOARD` | `MART_OPEN_TRANSPORT.MART_SWISS_RAIL_OVERVIEW` | ~4,300 |
| `dbt_weather` | `SFG_ENTERPRISE.DCM.DBT_WEATHER` | `RAW_WEATHER.METEOSWISS_MEASUREMENTS` | `MART_WEATHER.MART_WEATHER_STATION_CATALOG` | ~9,300 |

**Pattern** (differs from seed-based dbt projects):
- Uses `source()` in `models/staging/schema.yml` pointing at RAW schemas (not `ref()` for seeds)
- Staging models use `LATERAL FLATTEN(input => raw:<array_key>)` to extract from VARIANT arrays
- Timestamp fields with timezone offsets (`+0100`) require explicit format: `TO_TIMESTAMP_NTZ(val::string, 'YYYY-MM-DD"T"HH24:MI:SSTZHTZM')`
- No seeds directory -- data comes from live Openflow streams

## Semantic Views

3 semantic views materialized via dbt using `dbt_semantic_view` package:
- `SFG_ENTERPRISE.MART_FULFILLMENT.FULFILLMENT_ANALYTICS` -- order-to-delivery lifecycle (14 dims, 4 facts, 5 metrics)
- `SFG_ENTERPRISE.MART_REVENUE_ANALYTICS.REVENUE_ANALYTICS` -- revenue by shipping route (2 dims, 8 facts, 3 metrics)
- `SFG_ENTERPRISE.MART_COMPLIANCE.COMPLIANCE_ANALYTICS` -- FINMA/BAZG/GwG compliance (13 dims, 1 fact, 5 metrics)

## Cortex Agent

- Agent: `SFG_ADMIN.AGENTS.FULFILLMENT_ANALYST`
- Spec: `cortex-agent/fulfillment_analyst_spec.json`
- 3 Analyst tools (one per semantic view), warehouse: `SWISSFLAKES_WH_CORTEX`
- Bilingual DE/EN, Swiss regulatory context (FINMA, BAZG, GwG)

## Streamlit Apps (SiS)

Deployed via `snow streamlit deploy` (NOT DCM). Each app has its own `snowflake.yml`.

| App | Location | Target DB.SCHEMA | Warehouse |
|-----|----------|------------------|----------|
| SFG_ENTERPRISE_DASHBOARD | streamlit-apps/sfg_enterprise/ | SFG_ENTERPRISE.MART_FULFILLMENT | SWISSFLAKES_WH_BI |
| SFG_ADMIN_DASHBOARD | streamlit-apps/sfg_admin/ | SFG_ADMIN.GOVERNANCE | SWISSFLAKES_WH_ADMIN |

- Multi-page pattern: `st.navigation()` + `views/` directory (NEVER `pages/` -- conflicts with legacy auto-discovery)
- Deploy: `snow streamlit deploy --project streamlit-apps/<app> --replace -c <connection>`
- Uses `snowflake.snowpark.context.get_active_session()` for data access

## Snowflake Notebooks

Deployed via `snow notebook deploy` (NOT DCM). Each notebook has its own `snowflake.yml`.

| Notebook | Location | Target DB.SCHEMA | Warehouse |
|----------|----------|------------------|----------|
| SFG_ENTERPRISE_EXPLORATION | notebooks/sfg_enterprise_exploration/ | SFG_ENTERPRISE.MART_FULFILLMENT | SWISSFLAKES_WH_BI |
| COMPLIANCE_ANALYSIS | notebooks/compliance_analysis/ | SFG_ENTERPRISE.MART_COMPLIANCE | SWISSFLAKES_WH_COMPLIANCE |

- Deploy: `snow notebook deploy --project notebooks/<name> --replace -c <connection>`

## Openflow (Open Data Ingestion)

9 Openflow flows ingest Swiss/European open data into RAW schemas via Snowpipe Streaming.
All sources are credential-free and Marketplace-eligible.

| Flow | Source | Target | Schedule |
|------|--------|--------|----------|
| transport_opendata_ch | transport.opendata.ch | SFG_LOGISTICS.RAW_LOCATIONS.TRANSPORT_CONNECTIONS | 5 min |
| ecb_exchange_rates | ECB SDMX API | SFG_PAY.RAW_TRANSACTIONS.ECB_EXCHANGE_RATES | 1 day |
| sbb_stationboard | SBB stationboard | SFG_LOGISTICS.RAW_SHIPMENTS.SBB_STATIONBOARD | 1 min |
| sbb_ist_daten | SBB Ist-Daten | SFG_LOGISTICS.RAW_SHIPMENTS.SBB_IST_DATEN | 1 day |
| meteoswiss | MeteoSwiss OGD | SFG_ENTERPRISE.RAW_WEATHER.METEOSWISS_MEASUREMENTS | 10 min |
| swisstopo | swisstopo boundaries | SFG_LOGISTICS.RAW_LOCATIONS.SWISSTOPO_BOUNDARIES | 1 day |
| bazg_foreign_trade | BAZG customs | SFG_LOGISTICS.RAW_SHIPMENTS.BAZG_FOREIGN_TRADE | 1 day |
| astra_traffic | ASTRA traffic counts | SFG_LOGISTICS.RAW_FLEET.ASTRA_TRAFFIC_COUNTS | 1 day |
| plz_directory | Swiss PLZ directory | SFG_LOGISTICS.RAW_LOCATIONS.SWISS_PLZ_DIRECTORY | 1 day |

- Flow scripts subclass `OpenflowFlowBuilder` in `openflow/shared/flow_builder.py`
- Session config read from openflow infrastructure cache (`~/.snowflake/cortex/memory/openflow_infrastructure_*.json`)
- Deploy all: `./openflow/deploy.sh --account <ACCOUNT> [--profile <PROFILE>]`
- Deploy single: `python -m openflow.flows.<flow_name> --account <ACCOUNT>`
- Requires: `openflow` skill (session/profile management), `openflow-layout` skill (canvas arrangement)
- EAI: 6 egress domains in `infrastructure/terraform/openflow_eai.tf`
- Grants: `infrastructure/terraform/openflow_grants.tf` (OPENFLOW_ADMIN -> RAW schemas)

## Directory Map

```
data_products/{name}/                    -- DCM project (manifest.yml + sources/)
data_products/{name}/sources/definitions/ -- DCM SQL definitions (01_infra, 02_dbt_*)
data_products/{name}/sources/dbt_{dp}/   -- Embedded dbt projects (one per sub-DP)
data_products/{name}/sources/dbt_{dp}/models/listings/ -- Listing model + schema.yml per sub-DP
data_products/{name}/sources/dbt_{dp}/packages.yml     -- dbt-snowflake-listings dependency
streamlit-apps/{app}/                    -- Streamlit in Snowflake apps (snowflake.yml + views/)
notebooks/{name}/                        -- Snowflake Notebooks (snowflake.yml + .ipynb)
cortex-agent/                            -- Cortex Agent spec + creation SQL
openflow/                                -- Openflow flow scripts (open data ingestion)
openflow/shared/flow_builder.py          -- Base class for KuCoin v2 pattern
openflow/flows/                          -- Individual flow scripts (one per source)
openflow/deploy.sh                       -- Orchestrator: deploy all flows sequentially
infrastructure/terraform/                -- Security policies, monitors, EAI, grants
tests/                                   -- DCM validation tests
docs/                                    -- Workshop guide
```

## Known Issues / Resolution Patterns

### DCM First-Deploy Chicken-and-Egg
`DEFINE DBT PROJECT` in `02_dbt_*.sql` validates during `PLAN_FOR_DEPLOY` before `DEFINE SCHEMA` in `01_infrastructure.sql` takes effect. New schemas + new dbt projects require a two-pass deploy:
1. Temporarily rename `02_dbt_new.sql` to `02_dbt_new.sql.hold`
2. `snow dcm deploy ... --target PROD` -- creates schemas + grants
3. Restore file, deploy again -- dbt project validates successfully
Subsequent deploys work in a single pass.

### Invalid Snowpipe Streaming Pipes
When SSV2 creates a pipe before the target table exists, the pipe gets `invalid_reason: "Table does not exist"` and cannot be dropped (Snowflake-managed, owner=None). Fix:
1. `CREATE OR REPLACE TABLE <target> (RAW VARIANT)` -- recreates table, invalidates old pipe
2. Re-grant `INSERT, EVOLVE SCHEMA ON TABLE ... TO ROLE PUBLIC`
3. Stop/purge/restart the Openflow flow -- SSV2 creates a fresh valid pipe

### DCM Deploy Requires --target Flag
On Snow CLI 3.16.0, `snow dcm deploy` fails when `manifest.yml` uses Jinja templating without `--target PROD`. Always pass the target flag.

## Verification

After any change, run:
```bash
grep -r "ahuck\|he80908\|ANTON\|SFSEEUROPE" . --include='*.yml' --include='*.yaml' --include='*.sql' --include='*.md' --include='*.tf' --include='*.py' --include='*.json'
```
Must return 0 matches.
