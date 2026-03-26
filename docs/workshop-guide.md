# SwissFlakes Group -- Workshop Guide

Step-by-step walkthrough for deploying and demonstrating the SwissFlakes Group data mesh.

## Architecture Overview

```
Source Layer (8 DPs)           Enterprise Layer (2 DPs)        Consumer Layer (2 DPs)
+------------------+          +---------------------+         +---------------------+
| SHIPMENTS        |---+      | FULFILLMENT         |---+     | REVENUE_ANALYTICS   |
| FLEET            |---+----->| (order-to-delivery)  |   +--->| (route profitability)|
| LOCATIONS        |---+      +---------------------+   |     +---------------------+
| ORDERS           |---+                                 |
| CUSTOMERS        |---+      +---------------------+   |     +---------------------+
| PRODUCTS         |---+----->| CUSTOMER_360         |---+--->| COMPLIANCE           |
| TRANSACTIONS     |---+      | (full customer view) |         | (FINMA/BAZG/GwG)    |
| MERCHANTS        |---+      +---------------------+         +---------------------+
+------------------+
                                                                       |
                                                                       v
                                                               +------------------+
                                                               | Cortex Agent     |
                                                               | (3 Semantic Views)|
                                                               +------------------+
```

## Prerequisites

1. Snowflake account with ACCOUNTADMIN
2. [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli) installed
3. Snow CLI connection configured (e.g., `snow connection add`)

## Step 1: Platform Infrastructure (T2)

Deploy the platform DCM project that creates the admin database, warehouses, platform roles, and governance tags.

```bash
snow dcm create SWISSFLAKES_ADMIN.DCM.PLATFORM --if-not-exists -c <connection>
snow dcm deploy SWISSFLAKES_ADMIN.DCM.PLATFORM -c <connection> --alias "initial"
```

Verify:
```sql
SHOW WAREHOUSES LIKE 'SWISSFLAKES_WH_%';   -- 8 warehouses
SHOW ROLES LIKE 'SWISSFLAKES_%';           -- 6 platform roles
SHOW TAGS IN SCHEMA SWISSFLAKES_ADMIN.GOVERNANCE;  -- 9 tags
```

## Step 2: Source Data Products (T3 + T4)

For each source DP (SHIPMENTS, FLEET, LOCATIONS, ORDERS, CUSTOMERS, PRODUCTS, TRANSACTIONS, MERCHANTS):

```bash
snow dcm create {DB}.DCM.DATA_PRODUCT --if-not-exists -c <connection>
snow dcm deploy {DB}.DCM.DATA_PRODUCT -c <connection> --alias "initial"
```

Load seed data and build models via Snowflake-native dbt:
```sql
EXECUTE DBT PROJECT {DB}.DCM.DBT_{DB} ARGS = 'seed';
EXECUTE DBT PROJECT {DB}.DCM.DBT_{DB} ARGS = 'run';
```

Verify:
```sql
SELECT COUNT(*) FROM ORDERS.RAW.ORDER_HEADER;           -- ~100
SELECT COUNT(*) FROM TRANSACTIONS.RAW.PAYMENT;          -- ~150
SELECT COUNT(*) FROM CUSTOMERS.RAW.BUSINESS_CUSTOMER;   -- ~30
```

## Step 3: Internal Marketplace Listings (T6)

Publish each source DP's MARTS tables via organization listings:

```sql
CREATE SHARE IF NOT EXISTS SWISSFLAKES_{DP}_SHARE;
GRANT USAGE ON DATABASE {DB} TO SHARE SWISSFLAKES_{DP}_SHARE;
GRANT USAGE ON SCHEMA {DB}.MARTS TO SHARE SWISSFLAKES_{DP}_SHARE;
GRANT SELECT ON ALL TABLES IN SCHEMA {DB}.MARTS TO SHARE SWISSFLAKES_{DP}_SHARE;

CREATE ORGANIZATION LISTING SWISSFLAKES_{DP}_LISTING
  SHARE SWISSFLAKES_{DP}_SHARE AS
$$
title: "SwissFlakes {DP} Data Product"
description: "MARTS tables from the {DP} source data product"
terms_of_service:
  type: OFFLINE
targets:
  accounts: ["IN ORGANIZATION"]
$$;
```

Verify:
```sql
SHOW SHARES LIKE 'SWISSFLAKES_%';
SHOW ORGANIZATION LISTINGS LIKE 'SWISSFLAKES_%';
```

## Step 4: Enterprise + Consumer Data Products (T7)

Deploy infrastructure and run cross-database dbt models for FULFILLMENT, CUSTOMER_360, REVENUE_ANALYTICS, COMPLIANCE:

```bash
snow dcm create {DB}.DCM.DATA_PRODUCT --if-not-exists -c <connection>
snow dcm deploy {DB}.DCM.DATA_PRODUCT -c <connection> --alias "initial"
```

```sql
EXECUTE DBT PROJECT {DB}.DCM.DBT_{DB} ARGS = 'run';
```

Verify:
```sql
SELECT COUNT(*) FROM FULFILLMENT.MARTS.FULFILLMENT_LIFECYCLE;    -- 150
SELECT COUNT(*) FROM CUSTOMER_360.MARTS.CUSTOMER_OVERVIEW;        -- 31
SELECT COUNT(*) FROM REVENUE_ANALYTICS.MARTS.REVENUE_BY_ROUTE;    -- 48
SELECT COUNT(*) FROM COMPLIANCE.MARTS.TRANSACTION_REPORT;          -- 150
```

## Step 5: Semantic Views + Cortex Agent (T8)

Deploy the 3 semantic views using the SQL DDL files:

```bash
snow sql -f semantic-views/fulfillment_analytics.sql -c <connection>
snow sql -f semantic-views/compliance_analytics.sql -c <connection>
snow sql -f semantic-views/revenue_analytics.sql -c <connection>
```

Deploy the Cortex Agent:
```bash
snow sql -f cortex-agent/create_agent.sql -c <connection>
```

## Step 6: Openflow Data Transformation (T9 continued)

After Openflow flows are running and streaming data into RAW tables, deploy dbt projects that transform the raw VARIANT data into analytics-ready marts.

### Architecture

```
Openflow Flows (live APIs)
    |
    v
RAW Tables (single VARIANT column "RAW")
    |  LATERAL FLATTEN
    v
STG Views (typed columns, one row per record)
    |
    v
MART Tables (analytics-ready, joined/unioned)
```

### Deploy via DCM

**Important**: New schemas + new dbt projects require a two-pass deploy (see Known Issues in AGENTS.md).

First deploy (infrastructure only -- creates schemas + grants):
```bash
# Temporarily hold back the dbt definition
mv data_products/sfg_logistics/sources/definitions/02_dbt_open_transport.sql \
   data_products/sfg_logistics/sources/definitions/02_dbt_open_transport.sql.hold

snow dcm deploy SFG_LOGISTICS.DCM.DP_SFG_LOGISTICS \
  --from data_products/sfg_logistics --target PROD -c <connection>

# Restore and deploy again
mv data_products/sfg_logistics/sources/definitions/02_dbt_open_transport.sql.hold \
   data_products/sfg_logistics/sources/definitions/02_dbt_open_transport.sql

snow dcm deploy SFG_LOGISTICS.DCM.DP_SFG_LOGISTICS \
  --from data_products/sfg_logistics --target PROD -c <connection>
```

Repeat for SFG_ENTERPRISE with `02_dbt_weather.sql`.

### Execute dbt Projects

```sql
EXECUTE DBT PROJECT SFG_LOGISTICS.DCM.DBT_OPEN_TRANSPORT ARGS = 'run';
EXECUTE DBT PROJECT SFG_ENTERPRISE.DCM.DBT_WEATHER ARGS = 'run';
```

### Verify

```sql
-- Swiss rail data: ~4,300 rows from transport.opendata.ch + SBB stationboard
SELECT data_source, COUNT(*) AS row_count
FROM SFG_LOGISTICS.MART_OPEN_TRANSPORT.MART_SWISS_RAIL_OVERVIEW
GROUP BY data_source;

-- MeteoSwiss weather stations: ~9,300 stations with coordinates
SELECT COUNT(*) AS station_count,
       MIN(latitude) AS min_lat, MAX(latitude) AS max_lat
FROM SFG_ENTERPRISE.MART_WEATHER.MART_WEATHER_STATION_CATALOG;
```

## Demo Scenarios

### Scenario 1: Fulfillment Analytics
> "What is the average delivery time for Basel to Zurich shipments?"

The agent uses `fulfillment_analytics` tool to query `FULFILLMENT.MARTS.FULFILLMENT_LIFECYCLE`.

### Scenario 2: Revenue by Payment Method
> "Show total revenue by payment method"

The agent uses `fulfillment_analytics` tool to aggregate order totals by payment method.

### Scenario 3: Compliance / BAZG Customs
> "Which transactions require BAZG customs declarations?"

The agent uses `compliance_analytics` tool to query `COMPLIANCE.MARTS.TRANSACTION_REPORT` for customs-flagged transactions.

### Scenario 4: Revenue by Route (German)
> "Zeig mir den Nettoumsatz pro Strecke"

The agent uses `revenue_analytics` tool with Swiss German synonyms.

### Scenario 5: Swiss Rail Operations (Live Data)
```sql
-- Which train lines have the most delays?
SELECT line_text, product, operator,
       AVG(delay_minutes) AS avg_delay,
       COUNT(*) AS departures
FROM SFG_LOGISTICS.MART_OPEN_TRANSPORT.MART_SWISS_RAIL_OVERVIEW
WHERE delay_minutes > 0
GROUP BY line_text, product, operator
ORDER BY avg_delay DESC
LIMIT 10;
```

### Scenario 6: Weather Station Coverage
```sql
-- Weather stations by canton (approximate via coordinates)
SELECT station_name, latitude, longitude, num_assets
FROM SFG_ENTERPRISE.MART_WEATHER.MART_WEATHER_STATION_CATALOG
ORDER BY num_assets DESC
LIMIT 10;
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 1 DB per data product | Data mesh ownership boundaries |
| DCM for infrastructure | Declarative, idempotent, version-controlled |
| DEFINE DBT PROJECT | Snowflake-native dbt execution, no local install needed |
| Semantic Views (SQL DDL) | First-class Snowflake objects, SQL-based, no YAML stage files |
| Organization listings (SHARE) | Internal Marketplace discoverability without app packages |
| Cross-DB source() in dbt | Enterprise/consumer DPs reference source DP MARTS via database override |
| LATERAL FLATTEN for Openflow | Extract typed columns from single VARIANT column streamed by SSV2 |
| DATA_QUALITY tags | Quality encoding decoupled from schema names |
