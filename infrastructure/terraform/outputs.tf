output "masking_policy_names" {
  description = "Fully qualified names of all masking policies"
  value = {
    mask_email       = snowflake_masking_policy.mask_email.fully_qualified_name
    mask_phone       = snowflake_masking_policy.mask_phone.fully_qualified_name
    mask_iban        = snowflake_masking_policy.mask_iban.fully_qualified_name
    mask_credit_card = snowflake_masking_policy.mask_credit_card.fully_qualified_name
    mask_name        = snowflake_masking_policy.mask_name.fully_qualified_name
    mask_address     = snowflake_masking_policy.mask_address.fully_qualified_name
    mask_amount      = snowflake_masking_policy.mask_amount.fully_qualified_name
  }
}

output "row_access_policy_names" {
  description = "Fully qualified names of all row access policies"
  value = {
    rap_pii_data       = snowflake_row_access_policy.rap_pii_data.fully_qualified_name
    rap_financial_data = snowflake_row_access_policy.rap_financial_data.fully_qualified_name
    rap_customs_data   = snowflake_row_access_policy.rap_customs_data.fully_qualified_name
    rap_merchant_data  = snowflake_row_access_policy.rap_merchant_data.fully_qualified_name
  }
}

output "resource_monitor_names" {
  description = "Names of all resource monitors"
  value = {
    global = snowflake_resource_monitor.global.name
    cortex = snowflake_resource_monitor.cortex.name
  }
}
