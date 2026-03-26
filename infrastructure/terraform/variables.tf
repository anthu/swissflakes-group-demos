variable "governance_db" {
  description = "Database for governance objects"
  type        = string
  default     = "SWISSFLAKES_ADMIN"
}

variable "governance_schema" {
  description = "Schema for governance objects"
  type        = string
  default     = "GOVERNANCE"
}

variable "privileged_roles" {
  description = "Roles allowed to see unmasked data"
  type        = list(string)
  default = [
    "ACCOUNTADMIN",
    "SWISSFLAKES_PLATFORM_ADMIN",
    "SWISSFLAKES_COMPLIANCE_OFFICER"
  ]
}
