#!/usr/bin/env python3
"""
Flow: ASTRA Traffic Counts -> SFG_LOGISTICS.RAW_FLEET.ASTRA_TRAFFIC_COUNTS
Pattern: STAC annual CSV (yearly traffic volume data)

ASTRA (Swiss Federal Roads Office) publishes annual highway traffic counts
via the Federal STAC API. Updated once per year (end of year).

Same STAC pattern as MeteoSwiss/swisstopo — query items, store as VARIANT.

Learnings from Flows 1-7:
- Annual data: poll daily, STAC items won't change often
- Idempotent writes via Snowpipe Streaming offset tracking prevent duplicates
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class ASTRATrafficCounts(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "ASTRA Traffic Counts"

    @property
    def param_context_name(self) -> str:
        return "ASTRA Traffic Counts Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_FLEET",
            "Table": "ASTRA_TRAFFIC_COUNTS",
        }

    @property
    def api_url(self) -> str:
        return (
            "https://data.geo.admin.ch/api/stac/v1/collections/"
            "ch.astra.strassenverkehrszaehlung-uebergeordnetes-netz/items?limit=100"
        )

    @property
    def schedule_period(self) -> str:
        # Annual data — check daily
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/id"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy ASTRA Traffic Counts flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = ASTRATrafficCounts(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
