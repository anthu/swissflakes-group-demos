---
name: "openflow-open-data-deployment"
created: "2026-03-25T12:36:32.865Z"
status: pending
---

# Openflow Open Data Deployment Plan (v3 — Final)

## Decisions Confirmed

| Decision          | Answer                                                                               |
| ----------------- | ------------------------------------------------------------------------------------ |
| MeteoSwiss target | `SFG_ENTERPRISE.RAW_WEATHER` (new schema, DCM change required)                       |
| Execution         | Sequential sub-agents, pass learnings forward, produce a skill                       |
| Pipe naming       | Auto-created by PutSnowpipeStreaming2, `{TABLE}-STREAMING` convention, no DDL needed |

## Reference Pattern: KuCoin AllTickers v2

```
flowchart TD
    InvokeHTTP["InvokeHTTP\nFetch API"] --> JoltTransform["JoltTransformJSON\nWrap as VARIANT"]
    JoltTransform --> PutSnowpipe["PutSnowpipeStreaming2\nSNOWFLAKE_MANAGED auth"]
    PutSnowpipe -->|success| SuccessFunnel["Funnel\n5 min expiry"]
    PutSnowpipe -->|failure| Retry["RetryFlowFile\n1 retry"]
    Retry -->|retry| EnsureDest["Ensure Destination Exists\nchild PG"]
    Retry -->|retries_exceeded| FailFunnel["Funnel\n24h expiry"]
    EnsureDest --> PutSnowpipe

    subgraph ensureDest [Ensure Destination Exists - child PG]
        CreateDB["ExecuteSQLStatement\nCREATE DATABASE IF NOT EXISTS"] --> CreateSchema["UpdateSnowflakeSchema\nEnsure Schema"]
        CreateSchema --> CreateTable["ExecuteSQLStatement\nCREATE TABLE ... RAW VARIANT"]
    end
```

### Components

| Component        | Type                               | Config                                                                 |
| ---------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| Streaming writer | `PutSnowpipeStreaming2`            | Auth: `SNOWFLAKE_MANAGED`, Transfer: `ROWS`, Pipe: `{TABLE}-STREAMING` |
| JDBC connection  | `SnowflakeConnectionService`       | Auth: `SNOWFLAKE_MANAGED` (for DDL child PG)                           |
| HTTP client      | `StandardWebClientServiceProvider` | HTTP/2 (for PutSnowpipeStreaming2)                                     |
| JSON transform   | `JoltTransformJSON`                | Spec: `{"*":"RAW.&"}` wraps payload into VARIANT                       |
| Error handling   | `RetryFlowFile` (1 retry)          | Failure routes to self-healing DDL child PG                            |
| Target table     | Single `RAW VARIANT` column        | Raw ELT — all parsing deferred to dbt                                  |

---

## Repo Layout

```
openflow/
├── deploy.sh                          # Orchestrator: TF apply -> sequential flow builds
├── shared/
│   ├── __init__.py
│   └── flow_builder.py                # Base class encapsulating KuCoin v2 pattern
├── flows/
│   ├── transport_opendata_ch.py       # JSON API -> VARIANT -> Streaming2
│   ├── sbb_stationboard.py           # JSON API (1 min) -> VARIANT -> Streaming2
│   ├── sbb_ist_daten.py              # Daily CSV bulk -> VARIANT -> Streaming2
│   ├── ecb_exchange_rates.py          # Daily CSV -> VARIANT -> Streaming2
│   ├── meteoswiss.py                  # STAC 2-step -> CSV -> VARIANT -> Streaming2
│   ├── swisstopo.py                   # STAC 2-step -> GeoJSON -> VARIANT -> Streaming2
│   ├── bazg_foreign_trade.py          # ZIP -> CSV -> VARIANT -> Streaming2
│   ├── astra_traffic.py               # STAC annual -> CSV -> VARIANT -> Streaming2
│   └── plz_directory.py               # STAC quarterly -> CSV -> VARIANT -> Streaming2
infrastructure/terraform/
└── openflow_eai.tf                    # Network rule (6 domains) + EAI + grant
data_products/sfg_enterprise/sources/definitions/
└── 01_infrastructure.sql              # MODIFIED: add RAW_WEATHER schema + OPENFLOW_ADMIN grants
```

---

## Source -> Target Mapping

| # | Source                | Target DB.Schema.Table                                | Pattern             |
| - | --------------------- | ----------------------------------------------------- | ------------------- |
| 1 | transport.opendata.ch | SFG\_LOGISTICS.RAW\_LOCATIONS.TRANSPORT\_CONNECTIONS  | JSON API            |
| 2 | SBB stationboard      | SFG\_LOGISTICS.RAW\_SHIPMENTS.SBB\_STATIONBOARD       | JSON API (1 min)    |
| 3 | SBB Ist-Daten         | SFG\_LOGISTICS.RAW\_SHIPMENTS.SBB\_IST\_DATEN         | Daily CSV bulk      |
| 4 | ECB SDMX              | SFG\_PAY.RAW\_TRANSACTIONS.ECB\_EXCHANGE\_RATES       | Daily CSV           |
| 5 | MeteoSwiss            | SFG\_ENTERPRISE.RAW\_WEATHER.METEOSWISS\_MEASUREMENTS | STAC 2-step CSV     |
| 6 | swisstopo             | SFG\_LOGISTICS.RAW\_LOCATIONS.SWISSTOPO\_BOUNDARIES   | STAC 2-step GeoJSON |
| 7 | BAZG                  | SFG\_LOGISTICS.RAW\_SHIPMENTS.BAZG\_FOREIGN\_TRADE    | ZIP CSV             |
| 8 | ASTRA                 | SFG\_LOGISTICS.RAW\_FLEET.ASTRA\_TRAFFIC\_COUNTS      | STAC annual CSV     |
| 9 | PLZ                   | SFG\_LOGISTICS.RAW\_LOCATIONS.SWISS\_PLZ\_DIRECTORY   | STAC quarterly CSV  |

---

## Execution Strategy: Sequential Sub-agents with Knowledge Passing

```
flowchart LR
    SA1["Sub-agent 1\ntransport.opendata.ch\nSimplest JSON API"] --> L1["Learnings 1"]
    L1 --> SA2["Sub-agent 2\nECB exchange rates\nCSV variant"]
    SA2 --> L2["Learnings 1+2"]
    L2 --> SA3["Sub-agent 3\nSBB stationboard\nHigh-freq JSON"]
    SA3 --> L3["Learnings 1-3"]
    L3 --> SA4["Sub-agent 4\nSBB Ist-Daten\nBulk CSV download"]
    SA4 --> L4["Learnings 1-4"]
    L4 --> SA5["Sub-agent 5\nMeteoSwiss\nSTAC 2-step"]
    SA5 --> L5["Learnings 1-5"]
    L5 --> SA6["Sub-agent 6\nswisstopo\nGeoJSON"]
    SA6 --> L6["Learnings 1-6"]
    L6 --> SA7["Sub-agent 7\nBAZG\nZIP extraction"]
    SA7 --> L7["Learnings 1-7"]
    L7 --> SA8["Sub-agent 8\nASTRA traffic\nAnnual STAC"]
    SA8 --> L8["Learnings 1-8"]
    L8 --> SA9["Sub-agent 9\nPLZ directory\nQuarterly STAC"]
    SA9 --> Skill["Openflow REST\nIngestion Skill"]
```

### Ordering rationale

1. **transport.opendata.ch** — Simplest: single JSON GET, matches KuCoin v2 exactly
2. **ECB** — Introduces CSV format (CSVReader instead of JoltTransform)
3. **SBB stationboard** — High-frequency JSON (1 min cron)
4. **SBB Ist-Daten** — Daily bulk CSV download (different scheduling)
5. **MeteoSwiss** — Introduces STAC 2-step pattern (catalog query -> asset download)
6. **swisstopo** — STAC + GeoJSON (reuses STAC learnings)
7. **BAZG** — ZIP extraction (UnpackContent)
8. **ASTRA** — Annual STAC (simplest STAC variant)
9. **PLZ** — Quarterly STAC (simplest, validates all learnings)

### Knowledge accumulation per sub-agent

Each sub-agent receives:

- KuCoin v2 reference pattern (from /memories/kucoin\_v2\_reference\_pattern.md)
- Openflow skill references (`/openflow` + `/openflow-layout`)
- nipyapi path: `/Users/ahuck/.snowflake/cortex/skills/openflow/.venv/bin/nipyapi`
- Profile: `ahuck_antons_demo_runtime`
- Cumulative learnings from all previous sub-agents (error patterns, API quirks, nipyapi gotchas)

### Skill output

After all 9 flows, produce a skill file capturing:

- The shared flow builder pattern
- Source-pattern taxonomy (JSON API / CSV / STAC 2-step / ZIP)
- Common pitfalls and solutions encountered during building
- nipyapi API patterns for each component type
- Testing methodology (RUN\_ONCE, connection inspection)

---

## Task Details

### Task 1: Terraform EAI ✅ COMPLETE

infrastructure/terraform/openflow\_eai.tf — Network rule for 6 egress domains + EAI + grant to OPENFLOW\_ADMIN. User manually attaches via UI after `terraform apply`.

### Task 2: DCM — SFG\_ENTERPRISE RAW\_WEATHER ✅ COMPLETE

data\_products/sfg\_enterprise/sources/definitions/01\_infrastructure.sql — Already contains RAW\_WEATHER schema + OPENFLOW\_ADMIN grants.

### Task 3: Terraform — Openflow runtime grants ✅ COMPLETE

infrastructure/terraform/openflow\_grants.tf — Grants OPENFLOW\_ADMIN write access to RAW\_SHIPMENTS, RAW\_FLEET, RAW\_LOCATIONS (SFG\_LOGISTICS) and RAW\_TRANSACTIONS (SFG\_PAY). Note: SFG\_ENTERPRISE.RAW\_WEATHER grant handled by DCM (Task 2).

### Task 4: Shared flow builder

openflow/shared/flow\_builder.py — Base class encapsulating the full KuCoin v2 pattern. Sub-agents extend it.

### Task 5: Sequential sub-agent execution (9 flows)

Launch one sub-agent at a time. Each writes its flow script, deploys it to the runtime, validates with RUN\_ONCE, reports back learnings.

### Task 6: Deploy script

openflow/deploy.sh — Orchestrates TF + flow builds.

### Task 7: AGENTS.md update

Add openflow directory layout and deploy instructions.

### Task 8: Produce skill

Capture all learnings into a reusable skill for REST API ingestion via Openflow.
