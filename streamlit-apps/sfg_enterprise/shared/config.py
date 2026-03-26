ENTERPRISE_DB = "SFG_ENTERPRISE"
ADMIN_DB = "SFG_ADMIN"

SEMANTIC_VIEWS = {
    "fulfillment": f"{ENTERPRISE_DB}.MART_FULFILLMENT.FULFILLMENT_ANALYTICS",
    "revenue": f"{ENTERPRISE_DB}.MART_REVENUE_ANALYTICS.REVENUE_ANALYTICS",
    "compliance": f"{ENTERPRISE_DB}.MART_COMPLIANCE.COMPLIANCE_ANALYTICS",
}

AGENT_FQN = f"{ADMIN_DB}.AGENTS.FULFILLMENT_ANALYST"

WAREHOUSES = {
    "bi": "SWISSFLAKES_WH_BI",
    "cortex": "SWISSFLAKES_WH_CORTEX",
}

DOMAINS = {
    "SFG_LOGISTICS": {
        "label": "Logistics AG",
        "data_products": ["customers", "shipments", "fleet", "locations", "orders", "products"],
    },
    "SFG_PAY": {
        "label": "Pay AG",
        "data_products": ["transactions", "merchants"],
    },
    "SFG_ENTERPRISE": {
        "label": "Enterprise Analytics",
        "data_products": ["fulfillment", "customer_360", "revenue_analytics", "compliance"],
    },
}
