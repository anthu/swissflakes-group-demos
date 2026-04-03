resource "snowflake_network_rule" "github_egress" {
  name     = "SWISSFLAKES_GITHUB_EGRESS_RULE"
  database = "SFG_ADMIN"
  schema   = "GOVERNANCE"
  comment  = "Egress rule for GitHub dbt package downloads"
  type     = "HOST_PORT"
  mode     = "EGRESS"
  value_list = [
    "github.com",
    "codeload.github.com",
  ]
}

resource "snowflake_execute" "github_eai" {
  execute = <<-SQL
    CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SWISSFLAKES_GITHUB_EAI
      ALLOWED_NETWORK_RULES = (${snowflake_network_rule.github_egress.fully_qualified_name})
      ENABLED = TRUE
      COMMENT = 'EAI for GitHub dbt package downloads (dbt-snowflake-listings)'
  SQL
  revert = "DROP EXTERNAL ACCESS INTEGRATION IF EXISTS SWISSFLAKES_GITHUB_EAI"

  depends_on = [snowflake_network_rule.github_egress]
}

resource "snowflake_execute" "github_eai_grant_ci" {
  execute    = "GRANT USAGE ON INTEGRATION SWISSFLAKES_GITHUB_EAI TO ROLE SWISSFLAKES_PLATFORM_ADMIN"
  revert     = "REVOKE USAGE ON INTEGRATION SWISSFLAKES_GITHUB_EAI FROM ROLE SWISSFLAKES_PLATFORM_ADMIN"
  depends_on = [snowflake_execute.github_eai]
}
