#!/usr/bin/env python3
"""
Flow: BAZG Foreign Trade -> SFG_LOGISTICS.RAW_SHIPMENTS.BAZG_FOREIGN_TRADE
Pattern: ZIP CSV (download ZIP archive, extract CSV, stream as VARIANT)

BAZG (Swiss Federal Office for Customs and Border Security) publishes
import/export trade data as CSV files in ZIP archives, updated monthly.

The base builder's single InvokeHTTP fetches the ZIP. A future build_fetch_chain()
override will add UnpackContent to extract the CSV before Jolt transformation.
For now, the ZIP metadata URL is used to capture available datasets.

Learnings from Flows 1-6:
- ZIP extraction requires UnpackContent processor between InvokeHTTP and Jolt
- Monthly schedules need longer flowfile expiry on success funnels
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class BAZGForeignTrade(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "BAZG Foreign Trade"

    @property
    def use_groovy_json_wrapper(self) -> bool:
        return True

    @property
    def param_context_name(self) -> str:
        return "BAZG Foreign Trade Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_LOGISTICS",
            "Schema": "RAW_SHIPMENTS",
            "Table": "BAZG_FOREIGN_TRADE",
        }

    @property
    def api_url(self) -> str:
        return "https://ocean.nivel.bazg.admin.ch/open-data-reports/"

    @property
    def schedule_period(self) -> str:
        # Monthly — check daily, data arrives ~5th of month
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/period"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy BAZG Foreign Trade flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = BAZGForeignTrade(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
 