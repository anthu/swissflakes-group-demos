#!/usr/bin/env python3
"""
Flow: MeteoSwiss OGD -> SFG_ENTERPRISE.RAW_WEATHER.METEOSWISS_MEASUREMENTS
Pattern: STAC 2-step CSV (catalog query -> asset download)

MeteoSwiss publishes weather measurements via the Swiss Federal STAC API.
Step 1: Query STAC items endpoint for latest measurement assets
Step 2: Download CSV assets from the returned URLs

The base builder handles single-URL fetches. For the STAC 2-step pattern,
a future build_fetch_chain() override will add the catalog query step.
For now, this points at the STAC items endpoint which returns JSON metadata
that gets streamed as VARIANT for downstream dbt processing.

Learnings from Flows 1-4:
- STAC APIs return JSON with asset links — store metadata as VARIANT
- The actual CSV download can be handled by a second InvokeHTTP in a future
  build_fetch_chain() extension
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class MeteoSwiss(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "MeteoSwiss Measurements"

    @property
    def param_context_name(self) -> str:
        return "MeteoSwiss Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_ENTERPRISE",
            "Schema": "RAW_WEATHER",
            "Table": "METEOSWISS_MEASUREMENTS",
        }

    @property
    def api_url(self) -> str:
        return (
            "https://data.geo.admin.ch/api/stac/v1/collections/"
            "ch.meteoschweiz.ogd-smn/items?limit=100"
        )

    @property
    def schedule_period(self) -> str:
        return "10 min"

    @property
    def offset_pointer(self) -> str:
        return "/id"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy MeteoSwiss Measurements flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = MeteoSwiss(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
