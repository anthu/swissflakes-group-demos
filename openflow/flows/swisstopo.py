#!/usr/bin/env python3
"""
Flow: swisstopo -> SFG_LOGISTICS.RAW_LOCATIONS.SWISSTOPO_BOUNDARIES
Pattern: STAC 2-step GeoJSON (catalog query -> GeoJSON asset download)

swisstopo publishes Swiss administrative boundaries via the Federal STAC API.
Updated monthly (base maps) and quarterly (boundaries).

Same STAC pattern as MeteoSwiss — query items endpoint, store metadata as VARIANT.
GeoJSON assets will be downloaded in a future build_fetch_chain() extension.

Learnings from Flows 1-5:
- STAC items endpoint returns paginated JSON — limit=100 works for catalog queries
- GeoJSON is just JSON — same Jolt VARIANT wrapping works
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class SwissTopoBoundaries(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "swisstopo Boundaries"

    @property
    def param_context_name(self) -> str:
        return "swisstopo Boundaries Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_LOCATIONS",
            "Table": "SWISSTOPO_BOUNDARIES",
        }

    @property
    def api_url(self) -> str:
        return "https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill/items?limit=100"

    @property
    def schedule_period(self) -> str:
        # Monthly check
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/id"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy swisstopo Boundaries flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = SwissTopoBoundaries(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
