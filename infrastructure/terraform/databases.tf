locals {
  databases_config = yamldecode(file("${path.module}/databases.yml"))
  databases        = { for db in local.databases_config.databases : db.name => db }
  # Domain databases = everything except SFG_ADMIN (the platform DB)
  domain_databases = { for db in local.databases_config.databases : db.name => db if db.name != "SFG_ADMIN" }
}

# --- Databases and DCM schemas (driven by databases.yml) ---

resource "snowflake_database" "domain" {
  for_each = local.databases

  name                        = each.key
  comment                     = each.value.description
  data_retention_time_in_days = 1
}

resource "snowflake_schema" "dcm" {
  for_each = local.databases

  database     = snowflake_database.domain[each.key].name
  name         = "DCM"
  is_transient = "false"
  comment      = "Database Change Management project schema for ${each.key}"
}

# --- Role ownership bootstrap (no native resource for role ownership) ---

# USERADMIN owns platform roles (one-time bootstrap, not derivable from YAML)
resource "snowflake_execute" "platform_role_ownership" {
  execute = <<-SQL
    BEGIN
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_PLATFORM_ADMIN TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_DATA_ENGINEER TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_DATA_ANALYST TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_COMPLIANCE_OFFICER TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_CORTEX_ANALYST TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SWISSFLAKES_BI_CONSUMER TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SFG_LOGISTICS_DATA_PUBLISHER TO ROLE USERADMIN COPY CURRENT GRANTS;
      GRANT OWNERSHIP ON ROLE SFG_PAY_DATA_PUBLISHER TO ROLE USERADMIN COPY CURRENT GRANTS;
    END;
  SQL
  revert = "SELECT 1"
}

# USERADMIN owns each domain OWNER role (derived from database name convention)
resource "snowflake_execute" "domain_owner_role_ownership" {
  for_each = local.domain_databases

  execute = "GRANT OWNERSHIP ON ROLE DP_${each.key}_OWNER TO ROLE USERADMIN COPY CURRENT GRANTS"
  revert  = "GRANT OWNERSHIP ON ROLE DP_${each.key}_OWNER TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS"

  depends_on = [snowflake_execute.platform_role_ownership]
}

# --- Native grants (DRY, driven by databases.yml) ---

# Each domain OWNER role needs CREATE ROLE on account (for DCM DEFINE ROLE)
resource "snowflake_grant_privileges_to_account_role" "domain_owner_create_role" {
  for_each = local.domain_databases

  account_role_name = "DP_${each.key}_OWNER"
  privileges        = ["CREATE ROLE"]
  on_account        = true

  depends_on = [snowflake_execute.domain_owner_role_ownership]
}

# --- Admin DCM project ownership ---

resource "snowflake_execute" "admin_dcm_project_ownership" {
  execute = "GRANT OWNERSHIP ON DCM PROJECT SFG_ADMIN.DCM.PLATFORM TO ROLE USERADMIN COPY CURRENT GRANTS"
  revert  = "GRANT OWNERSHIP ON DCM PROJECT SFG_ADMIN.DCM.PLATFORM TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS"

  depends_on = [snowflake_schema.dcm["SFG_ADMIN"]]
}
