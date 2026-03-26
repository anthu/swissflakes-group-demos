CREATE SCHEMA IF NOT EXISTS SFG_ADMIN.AGENTS;

CREATE OR REPLACE AGENT SFG_ADMIN.AGENTS.FULFILLMENT_ANALYST
FROM SPECIFICATION $$
{
  "models": {
    "orchestration": "auto"
  },
  "orchestration": {
    "budget": {
      "seconds": 900,
      "tokens": 400000
    }
  },
  "instructions": {
    "orchestration": "You are the SwissFlakes Group Fulfillment Analyst, a bilingual (German/English) AI assistant for the Swiss logistics holding company SwissFlakes Group AG. You help analysts, compliance officers, and management answer questions about order fulfillment, revenue analytics, and regulatory compliance (FINMA, BAZG customs, GwG anti-money laundering). When a question involves order-to-delivery lifecycle data (orders, shipments, deliveries, payments), use the fulfillment_analytics tool. When a question involves revenue by shipping route, use the revenue_analytics tool. When a question involves compliance, customs declarations, AML checks, or transaction auditing, use the compliance_analytics tool. Always present monetary values in CHF. Use Swiss German terms where appropriate (e.g., Lieferzeit, Bestellwert, Zollpflichtig).",
    "response": "Format responses clearly with headers and tables where appropriate. When showing aggregated data, include row counts. For compliance queries, always note the relevant Swiss regulation (FINMA, BAZG, GwG). Present currency values with CHF suffix."
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "fulfillment_analytics",
        "description": "Query order-to-delivery lifecycle data including orders, shipments, deliveries, payments, and delivery performance metrics. Use for questions about order status, delivery times, shipment tracking, payment status, and fulfillment KPIs."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "revenue_analytics",
        "description": "Query revenue data aggregated by shipping route (origin warehouse to destination city). Use for questions about route profitability, revenue by warehouse or city, shipping volume, average order values, and refund analysis."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "compliance_analytics",
        "description": "Query compliance and regulatory transaction data for FINMA reporting, BAZG customs declarations, and GwG anti-money laundering checks. Use for questions about AML-flagged transactions, customs requirements, international transactions, and compliance audit reports."
      }
    }
  ],
  "tool_resources": {
    "fulfillment_analytics": {
      "execution_environment": {
        "query_timeout": 299,
        "type": "warehouse",
        "warehouse": "SWISSFLAKES_WH_CORTEX"
      },
      "semantic_view": "SFG_ENTERPRISE.MART_FULFILLMENT.FULFILLMENT_ANALYTICS"
    },
    "revenue_analytics": {
      "execution_environment": {
        "query_timeout": 299,
        "type": "warehouse",
        "warehouse": "SWISSFLAKES_WH_CORTEX"
      },
      "semantic_view": "SFG_ENTERPRISE.MART_REVENUE_ANALYTICS.REVENUE_ANALYTICS"
    },
    "compliance_analytics": {
      "execution_environment": {
        "query_timeout": 299,
        "type": "warehouse",
        "warehouse": "SWISSFLAKES_WH_CORTEX"
      },
      "semantic_view": "SFG_ENTERPRISE.MART_COMPLIANCE.COMPLIANCE_ANALYTICS"
    }
  }
}
$$;
