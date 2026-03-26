resource "snowflake_network_rule" "opendata_egress" {
  name     = "SWISSFLAKES_OPENDATA_EGRESS_RULE"
  database = "ADMIN_DB"
  schema   = "NETWORK_POLICY_MGMT"
  comment  = "Egress rule for SwissFlakes open data sources"
  type     = "HOST_PORT"
  mode     = "EGRESS"
  value_list = [
    "transport.opendata.ch",
    "data.opentransportdata.swiss",
    "data.sbb.ch",
    "data-api.ecb.europa.eu",
    "data.geo.admin.ch",
    "ocean.nivel.bazg.admin.ch",
  ]
}

resource "snowflake_execute" "opendata_eai" {
  execute = <<-SQL
    CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SWISSFLAKES_OPENDATA_EAI
      ALLOWED_NETWORK_RULES = (${snowflake_network_rule.opendata_egress.fully_qualified_name})
      ENABLED = TRUE
      COMMENT = 'EAI for SwissFlakes open data ingestion via Openflow'
  SQL
  revert = "DROP EXTERNAL ACCESS INTEGRATION IF EXISTS SWISSFLAKES_OPENDATA_EAI"

  depends_on = [snowflake_network_rule.opendata_egress]
}

resource "snowflake_execute" "opendata_eai_grant" {
  execute    = "GRANT USAGE ON INTEGRATION SWISSFLAKES_OPENDATA_EAI TO ROLE OPENFLOW_ADMIN"
  revert     = "REVOKE USAGE ON INTEGRATION SWISSFLAKES_OPENDATA_EAI FROM ROLE OPENFLOW_ADMIN"
  depends_on = [snowflake_execute.opendata_eai]
}
