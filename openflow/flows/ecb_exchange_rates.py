#!/usr/bin/env python3
"""
Flow: ECB SDMX API -> SFG_PAY.RAW_TRANSACTIONS.ECB_EXCHANGE_RATES
Pattern: Daily CSV (format=csvdata endpoint, polled on weekday schedule)

ECB publishes exchange rates for CHF, USD, GBP, JPY against EUR daily at ~16:00 CET.
The csvdata format returns CSV directly — no JSON wrapping needed, but we still use
JoltTransformJSON after converting CSV lines to JSON records.

Learnings from Flow 1 (transport.opendata.ch):
- The base builder handles the full KuCoin v2 pattern (InvokeHTTP -> Jolt -> Streaming)
- For CSV responses, the Jolt spec wraps the entire response body as a single VARIANT
  (same {"*":"RAW.&"} spec works since InvokeHTTP returns the body as-is)
"""
import argparse

from openflow.shared.flow_builder import OpenflowFlowBuilder


class ECBExchangeRates(OpenflowFlowBuilder):

    @property
    def flow_name(self) -> str:
        return "ECB Exchange Rates"

    @property
    def param_context_name(self) -> str:
        return "ECB Exchange Rates Params"

    def parameters(self) -> dict:
        return {
            "Database": "SFG_PAY",
            "Schema": "RAW_TRANSACTIONS",
            "Table": "ECB_EXCHANGE_RATES",
        }

    @property
    def api_url(self) -> str:
        return (
            "https://data-api.ecb.europa.eu/service/data/"
            "EXR/D.CHF+USD+GBP+JPY.EUR.SP00.A?format=csvdata"
        )

    @property
    def schedule_period(self) -> str:
        # Daily at 17:00 UTC (after ECB publishes at ~16:00 CET)
        return "1 day"

    @property
    def offset_pointer(self) -> str:
        return "/TIME_PERIOD"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy ECB Exchange Rates flow")
    parser.add_argument("--account", required=True, help="Snowflake account identifier")
    parser.add_argument("--role", default="OPENFLOW_ADMIN", help="Snowflake role")
    parser.add_argument("--profile", default=None, help="nipyapi profile (default: from cache)")
    args = parser.parse_args()

    builder = ECBExchangeRates(
        account=args.account, role=args.role, profile=args.profile
    )
    components = builder.build()
    print(f"\nDone. Process Group ID: {components.pg_id}")
