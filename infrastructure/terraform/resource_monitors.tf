resource "snowflake_resource_monitor" "global" {
  name         = "SWISSFLAKES_GLOBAL_MONITOR"
  credit_quota = 100

  notify_triggers           = [75]
  suspend_trigger           = 90
  suspend_immediate_trigger = 100

  frequency       = "MONTHLY"
  start_timestamp = "2026-04-01 00:00"
}

resource "snowflake_resource_monitor" "cortex" {
  name         = "SWISSFLAKES_CORTEX_MONITOR"
  credit_quota = 20

  notify_triggers           = [75]
  suspend_trigger           = 90
  suspend_immediate_trigger = 100

  frequency       = "MONTHLY"
  start_timestamp = "2026-04-01 00:00"
}
