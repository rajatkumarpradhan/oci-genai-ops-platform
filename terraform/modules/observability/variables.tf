variable "compartment_id" {
  type = string
}

variable "name_prefix" {
  type    = string
  default = "genaiops"
}

variable "alert_email" {
  type        = string
  description = "Email for alarm and budget notifications."
}

variable "monthly_budget" {
  type        = number
  description = "Monthly budget amount in the tenancy currency."
  default     = 100
  validation {
    condition     = var.monthly_budget > 0
    error_message = "monthly_budget must be positive."
  }
}
