resource "snowflake_row_access_policy" "rap_pii_data" {
  name     = "RAP_PII_DATA"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "PII_FLAG"
    type = "BOOLEAN"
  }

  body = <<-EOF
    case
      when current_role() in ('ACCOUNTADMIN', 'SWISSFLAKES_PLATFORM_ADMIN', 'SWISSFLAKES_COMPLIANCE_OFFICER') then true
      when PII_FLAG = false then true
      else false
    end
  EOF

  comment = "Restricts PII-tagged rows to compliance-approved roles (DSG/nFADP)"
}

resource "snowflake_row_access_policy" "rap_financial_data" {
  name     = "RAP_FINANCIAL_DATA"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "DATA_CLASSIFICATION"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in ('ACCOUNTADMIN', 'SWISSFLAKES_PLATFORM_ADMIN', 'SWISSFLAKES_COMPLIANCE_OFFICER') then true
      when current_role() in ('DP_TRANSACTIONS_OWNER', 'DP_TRANSACTIONS_READER', 'DP_REVENUE_ANALYTICS_OWNER', 'DP_REVENUE_ANALYTICS_READER') then true
      when DATA_CLASSIFICATION != 'FINMA_RESTRICTED' then true
      else false
    end
  EOF

  comment = "Restricts FINMA-regulated financial data to approved roles"
}

resource "snowflake_row_access_policy" "rap_customs_data" {
  name     = "RAP_CUSTOMS_DATA"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "CUSTOMS_FLAG"
    type = "BOOLEAN"
  }

  body = <<-EOF
    case
      when current_role() in ('ACCOUNTADMIN', 'SWISSFLAKES_PLATFORM_ADMIN', 'SWISSFLAKES_COMPLIANCE_OFFICER') then true
      when current_role() in ('DP_SHIPMENTS_OWNER', 'DP_COMPLIANCE_OWNER', 'DP_COMPLIANCE_READER') then true
      when CUSTOMS_FLAG = false then true
      else false
    end
  EOF

  comment = "Restricts BAZG customs-regulated data to approved roles"
}

resource "snowflake_row_access_policy" "rap_merchant_data" {
  name     = "RAP_MERCHANT_DATA"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "MERCHANT_OWNER_ROLE"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in ('ACCOUNTADMIN', 'SWISSFLAKES_PLATFORM_ADMIN', 'SWISSFLAKES_COMPLIANCE_OFFICER') then true
      when current_role() in ('DP_MERCHANTS_OWNER') then true
      when current_role() = MERCHANT_OWNER_ROLE then true
      else false
    end
  EOF

  comment = "Restricts merchant data to merchant owners and compliance roles"
}
