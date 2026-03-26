#!/usr/bin/env python3
"""
Flow: transport.opendata.ch -> SFG_LOGISTICS.RAW_LOCATIONS.TRANSPORT_CONNECTIONS
Pattern: Simple JSON API GET (closest to KuCoin v2 reference)
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class TransportOpendataCH(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "Transport Opendata CH"

    @property
    def param_context_name(self) -> str:
        return "Transport Opendata CH Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_LOCATIONS",
            "Table": "TRANSPORT_CONNECTIONS",
        }

    @property
    def api_url(self) -> str:
        return "https://transport.opendata.ch/v1/connections?from=Bern&to=Zurich&limit=6"

    @property
    def schedule_period(self) -> str:
        return "5 min"

    @property
    def offset_pointer(self) -> str:
        return "/from/departure/timestamp"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Transport Opendata CH flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = TransportOpendataCH(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
 