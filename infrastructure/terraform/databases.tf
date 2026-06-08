locals {
  databases_config = yamldecode(file("${path.module}/databases.yml"))
  databases        = { for db in local.databases_config.databases : db.name => db }
}

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
