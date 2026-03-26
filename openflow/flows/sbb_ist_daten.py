#!/usr/bin/env python3
"""
Flow: SBB Ist-Daten -> SFG_LOGISTICS.RAW_SHIPMENTS.SBB_IST_DATEN
Pattern: Daily bulk CSV download

SBB publishes actual vs planned train times as daily CSV files on
data.opentransportdata.swiss. Updated ~06:00 daily with previous day's data.
The CSV files are large (~200 MB/day) — streamed as VARIANT rows.

Learnings from Flows 1-3:
- Daily bulk files need longer read timeouts
- The base builder pattern works; just adjust schedule and timeout
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class SBBIstDaten(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "SBB Ist-Daten"

    @property
    def param_context_name(self) -> str:
        return "SBB Ist-Daten Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_SHIPMENTS",
            "Table": "SBB_IST_DATEN",
        }

    @property
    def api_url(self) -> str:
        return "https://data.opentransportdata.swiss/dataset/istdaten"

    @property
    def schedule_period(self) -> str:
        # Daily at 07:00 UTC (after SBB publishes at ~06:00)
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/BETRIEBSTAG"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy SBB Ist-Daten flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = SBBIstDaten(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
