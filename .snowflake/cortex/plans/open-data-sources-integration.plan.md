---
name: "open-data-sources-integration"
created: "2026-03-25T11:03:45.216Z"
status: pending
---

# Open Data Sources Integration Plan — SwissFlakes Group (v3)

## Overview

Integrate 8 public open data sources into the SwissFlakes Group demo project via Snowflake Openflow. All sources are credential-free and carry open licenses suitable for Marketplace redistribution.

## Data Sources (8 total)

### 1. transport.opendata.ch — Swiss Public Transport API

- **Endpoint**: `https://transport.opendata.ch/v1/connections`, `/v1/stationboard`, `/v1/locations`
- **Format**: JSON REST | **Auth**: None | **License**: MIT — **Marketplace: YES**
- **Refresh**: Real-time (poll every 5 min) | **Cron**: `*/5 * * * *`
- **Historical**: None — real-time only, start collecting from day 1
- **Target**: `SFG_LOGISTICS.RAW_LOCATIONS` | **Size**: \~5 MB/day

### 2. SBB Ist-Daten — Actual vs Planned Times

- **Endpoint**: `https://data.opentransportdata.swiss/dataset/istdaten` (bulk CSV) + `https://data.sbb.ch/api/` (stationboard)
- **Format**: CSV (bulk), JSON (stationboard) | **Auth**: None | **License**: OGD + attribution — **Marketplace: YES**
- **Refresh**: Stationboard 1 min; Ist-Daten daily \~06:00 | **Cron**: `*/1 * * * *` / `0 7 * * *`
- **Historical**: **\~10 years** — monthly ZIP archive from 2016–present (\~1 GB/month, \~100 GB total)
- **Target**: `SFG_LOGISTICS.RAW_FLEET`, `SFG_LOGISTICS.RAW_SHIPMENTS` | **Size**: \~200 MB/day

### 3. ECB SDMX API — Exchange Rates

- **Endpoint**: `https://data-api.ecb.europa.eu/service/data/EXR/D.CHF+USD+GBP+JPY.EUR.SP00.A?format=csvdata`
- **Format**: CSV/JSON/SDMX-ML | **Auth**: None | **License**: ECB © + attribution — **Marketplace: YES**
- **Refresh**: Daily \~16:00 CET (TARGET working days) | **Cron**: `0 17 * * 1-5`
- **Historical**: **25+ years** — full EXR history back to 1999. Total: \~2 MB
- **Incremental**: `updatedAfter` param + `If-Modified-Since` header
- **Target**: `SFG_PAY.RAW_TRANSACTIONS` (reference table) | **Size**: \~50 KB/day

### 4. MeteoSwiss — Weather Measurements & Forecasts

- **Endpoint**: `https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn`
- **Format**: CSV (via STAC API) | **Auth**: None | **License**: CC BY 4.0 — **Marketplace: YES**
- **Refresh**: Every 10 min (measurements), daily (forecasts) | **Cron**: `*/10 * * * *` / `0 6 * * *`
- **Historical**: **140+ years** — from \~1864 (monthly), 1981 (daily), 2004 (10-min). Total: \~5–10 GB
- **Target**: `SFG_ENTERPRISE.RAW_*` | **Size**: \~100 MB/day

### 5. swisstopo — Geographic / Admin Boundaries

- **Endpoint**: `https://data.geo.admin.ch/api/stac/v1/` (STAC catalog)
- **Format**: GeoJSON / GeoTIFF | **Auth**: None | **License**: OGD — **Marketplace: YES**
- **Refresh**: Monthly (base maps), quarterly (boundaries) | **Cron**: `0 3 1 * *`
- **Historical**: Full current geodata archive. Total: \~50 GB full or \~500 MB (admin boundaries only)
- **Target**: `SFG_LOGISTICS.RAW_LOCATIONS` | **Size**: <1 MB/day incremental

### 6. BAZG Foreign Trade — Swiss Customs Import/Export Data

- **Endpoint**: `https://ocean.nivel.bazg.admin.ch/open-data-reports/` (CSV ZIPs per tariff/country)
- **Format**: CSV | **Auth**: None | **License**: OGD + attribution — **Marketplace: YES**
- **Refresh**: Monthly | **Cron**: `0 4 5 * *` (5th of each month)
- **Historical**: **Multi-year** — trade data by country (CPA6) and by tariff number available as bulk downloads
- **Target**: `SFG_LOGISTICS.RAW_SHIPMENTS` (trade context) | **Size**: \~50 MB/month

### 7. ASTRA Road Traffic Counts — Highway Traffic Volumes

- **Endpoint**: `https://data.geo.admin.ch/api/stac/v1/collections/ch.astra.strassenverkehrszaehlung-uebergeordnetes-netz`
- **Format**: CSV / Shapefile | **Auth**: None | **License**: OGD + attribution — **Marketplace: YES**
- **Refresh**: Annually (yearly aggregates), updated end of year | **Cron**: `0 3 15 1 *` (Jan 15)
- **Historical**: **10+ years** — annual traffic volumes on national road network
- **Target**: `SFG_LOGISTICS.RAW_FLEET` (route planning context) | **Size**: \~20 MB/year

### 8. Swiss PLZ Directory — Postal Code Reference

- **Endpoint**: `https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo-vd.ortschaftenverzeichnis_plz`
- **Format**: CSV / GeoJSON | **Auth**: None | **License**: OGD + attribution — **Marketplace: YES**
- **Refresh**: Quarterly | **Cron**: `0 3 1 */3 *` (1st of every 3rd month)
- **Historical**: Current snapshot (reference data, no time series)
- **Target**: `SFG_LOGISTICS.RAW_LOCATIONS`, `SFG_PAY.RAW_MERCHANTS` (geocoding) | **Size**: \~2 MB/quarter

---

## Summary Table

| # | Source                | Auth | Refresh         | Historical           | Marketplace | Target DB                 |
| - | --------------------- | ---- | --------------- | -------------------- | ----------- | ------------------------- |
| 1 | transport.opendata.ch | None | 5 min           | None (forward only)  | YES         | SFG\_LOGISTICS            |
| 2 | SBB Ist-Daten         | None | 1 min / daily   | 10 years (\~100 GB)  | YES         | SFG\_LOGISTICS            |
| 3 | ECB SDMX API          | None | Daily 16:00 CET | 25+ years (\~2 MB)   | YES         | SFG\_PAY                  |
| 4 | MeteoSwiss            | None | 10 min / daily  | 140+ years (\~10 GB) | YES         | SFG\_ENTERPRISE           |
| 5 | swisstopo             | None | Monthly         | Full archive         | YES         | SFG\_LOGISTICS            |
| 6 | BAZG Foreign Trade    | None | Monthly         | Multi-year           | YES         | SFG\_LOGISTICS            |
| 7 | ASTRA Traffic Counts  | None | Annually        | 10+ years            | YES         | SFG\_LOGISTICS            |
| 8 | Swiss PLZ Directory   | None | Quarterly       | Current snapshot     | YES         | SFG\_LOGISTICS + SFG\_PAY |

**Credentials needed: ZERO across all 8 sources.** **Marketplace eligible: ALL 8 sources (with attribution).**

---

## Sizing

- **Daily volume**: \~310 MB/day (dominated by SBB Ist-Daten + MeteoSwiss)
- **Initial backfill**: \~110 GB (SBB archive + MeteoSwiss historical + ECB 25yr)
- **Compute**: 1 node of `SYSTEM_COMPUTE_POOL_CPU` (CPU\_X64\_S) is sufficient
- **Credit impact**: \~0.5–1 credit/day, well within 100 credit/month budget

---

## EAI Domains Required

All sources need egress network rules for Openflow. Domains to whitelist:

1. `transport.opendata.ch`
2. `data.opentransportdata.swiss`
3. `data.sbb.ch`
4. `data-api.ecb.europa.eu`
5. `data.geo.admin.ch` (MeteoSwiss + swisstopo + ASTRA + PLZ)
6. `ocean.nivel.bazg.admin.ch`

Note: domains 4–8 share `data.geo.admin.ch` except ECB and BAZG — only **6 distinct domains** needed.
