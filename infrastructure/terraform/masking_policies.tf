locals {
  privileged_roles_sql = join(", ", [for r in var.privileged_roles : "'${r}'"])
}

resource "snowflake_masking_policy" "mask_email" {
  name     = "MASK_EMAIL"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else concat(left(VAL, 1), '***@', split_part(VAL, '@', 2))
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks email addresses, showing first character and domain"
}

resource "snowflake_masking_policy" "mask_phone" {
  name     = "MASK_PHONE"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else concat('***-', right(VAL, 4))
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks phone numbers, showing last 4 digits"
}

resource "snowflake_masking_policy" "mask_iban" {
  name     = "MASK_IBAN"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else concat(left(VAL, 4), repeat('*', length(VAL) - 8), right(VAL, 4))
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks IBAN numbers, showing first 4 and last 4 characters"
}

resource "snowflake_masking_policy" "mask_credit_card" {
  name     = "MASK_CREDIT_CARD"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else concat('****-****-****-', right(VAL, 4))
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks credit card numbers, showing last 4 digits"
}

resource "snowflake_masking_policy" "mask_name" {
  name     = "MASK_NAME"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else '***'
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks personal names completely"
}

resource "snowflake_masking_policy" "mask_address" {
  name     = "MASK_ADDRESS"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "VARCHAR"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else '*** REDACTED ***'
    end
  EOF

  return_data_type = "VARCHAR"
  comment          = "Masks street addresses completely"
}

resource "snowflake_masking_policy" "mask_amount" {
  name     = "MASK_AMOUNT"
  database = var.governance_db
  schema   = var.governance_schema

  argument {
    name = "VAL"
    type = "NUMBER(38,2)"
  }

  body = <<-EOF
    case
      when current_role() in (${local.privileged_roles_sql}) then VAL
      else null
    end
  EOF

  return_data_type = "NUMBER(38,2)"
  comment          = "Masks financial amounts for unauthorized roles"
}
