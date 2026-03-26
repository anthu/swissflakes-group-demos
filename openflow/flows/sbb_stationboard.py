#!/usr/bin/env python3
"""
Flow: SBB Stationboard API -> SFG_LOGISTICS.RAW_SHIPMENTS.SBB_STATIONBOARD
Pattern: High-frequency JSON API (1 min poll)

SBB stationboard provides real-time departure/arrival data for Swiss train stations.
Uses the open SBB API (data.sbb.ch) which returns JSON.

Learnings from Flows 1-2:
- High-frequency polling (1 min) needs careful offset tracking to avoid duplicates
- The base builder's InvokeHTTP + Jolt + Streaming pattern works for JSON APIs
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class SBBStationboard(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "SBB Stationboard"

    @property
    def param_context_name(self) -> str:
        return "SBB Stationboard Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_SHIPMENTS",
            "Table": "SBB_STATIONBOARD",
        }

    @property
    def api_url(self) -> str:
        return "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/actual-data-sbb-previous-day/records?limit=100"

    @property
    def schedule_period(self) -> str:
        return "1 min"

    @property
    def offset_pointer(self) -> str:
        return "/stop_id"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy SBB Stationboard flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = SBBStationboard(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
