locals {
  openflow_target_schemas = {
    sfg_logistics_raw_shipments = {
      database = "SFG_LOGISTICS"
      schema   = "RAW_SHIPMENTS"
    }
    sfg_logistics_raw_fleet = {
      database = "SFG_LOGISTICS"
      schema   = "RAW_FLEET"
    }
    sfg_logistics_raw_locations = {
      database = "SFG_LOGISTICS"
      schema   = "RAW_LOCATIONS"
    }
    sfg_pay_raw_transactions = {
      database = "SFG_PAY"
      schema   = "RAW_TRANSACTIONS"
    }
  }
}

resource "snowflake_execute" "openflow_db_usage" {
  for_each = toset(distinct([for k, v in local.openflow_target_schemas : v.database]))

  execute = "GRANT USAGE ON DATABASE ${each.value} TO ROLE OPENFLOW_ADMIN"
  revert  = "REVOKE USAGE ON DATABASE ${each.value} FROM ROLE OPENFLOW_ADMIN"
}

resource "snowflake_execute" "openflow_schema_usage" {
  for_each = local.openflow_target_schemas

  execute = "GRANT USAGE ON SCHEMA ${each.value.database}.${each.value.schema} TO ROLE OPENFLOW_ADMIN"
  revert  = "REVOKE USAGE ON SCHEMA ${each.value.database}.${each.value.schema} FROM ROLE OPENFLOW_ADMIN"

  depends_on = [snowflake_execute.openflow_db_usage]
}

resource "snowflake_execute" "openflow_schema_create_table" {
  for_each = local.openflow_target_schemas

  execute = "GRANT CREATE TABLE ON SCHEMA ${each.value.database}.${each.value.schema} TO ROLE OPENFLOW_ADMIN"
  revert  = "REVOKE CREATE TABLE ON SCHEMA ${each.value.database}.${each.value.schema} FROM ROLE OPENFLOW_ADMIN"

  depends_on = [snowflake_execute.openflow_schema_usage]
}

resource "snowflake_execute" "openflow_schema_create_pipe" {
  for_each = local.openflow_target_schemas

  execute = "GRANT CREATE PIPE ON SCHEMA ${each.value.database}.${each.value.schema} TO ROLE OPENFLOW_ADMIN"
  revert  = "REVOKE CREATE PIPE ON SCHEMA ${each.value.database}.${each.value.schema} FROM ROLE OPENFLOW_ADMIN"

  depends_on = [snowflake_execute.openflow_schema_usage]
}
