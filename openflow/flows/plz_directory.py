#!/usr/bin/env python3
"""
Flow: Swiss PLZ Directory -> SFG_LOGISTICS.RAW_LOCATIONS.SWISS_PLZ_DIRECTORY
Pattern: STAC quarterly CSV (postal code reference data)

The Swiss PLZ directory is published by swisstopo via the Federal STAC API.
Updated quarterly — contains postal codes, municipality names, and coordinates.
Reference data used for geocoding across SFG_LOGISTICS and SFG_PAY.

Same STAC pattern as other geo.admin.ch sources.

Learnings from Flows 1-8:
- All STAC flows follow the same pattern: items endpoint -> VARIANT -> Streaming
- Reference data (no time series) — quarterly refresh is sufficient
- The build_fetch_chain() extension point is ready for STAC 2-step when needed
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class SwissPLZDirectory(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "Swiss PLZ Directory"

    @property
    def param_context_name(self) -> str:
        return "Swiss PLZ Directory Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_LOCATIONS",
            "Table": "SWISS_PLZ_DIRECTORY",
        }

    @property
    def api_url(self) -> str:
        return (
            "https://data.geo.admin.ch/api/stac/v1/collections/"
            "ch.swisstopo-vd.ortschaftenverzeichnis_plz/items?limit=100"
        )

    @property
    def schedule_period(self) -> str:
        # Quarterly data — check daily
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/id"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Swiss PLZ Directory flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = SwissPLZDirectory(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
