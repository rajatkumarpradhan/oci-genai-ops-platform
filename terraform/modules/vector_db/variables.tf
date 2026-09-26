variable "compartment_id" {
  type = string
}

variable "name_prefix" {
  type    = string
  default = "genaiops"
}

variable "db_name" {
  type    = string
  default = "genaiopsvec"
}

variable "is_free_tier" {
  type    = bool
  default = true
}

variable "admin_password" {
  type        = string
  sensitive   = true
  description = "ADB admin password; supply via TF_VAR, never commit."
}

variable "allowed_cidrs" {
  type        = list(string)
  description = "CIDRs allowed to reach the ADB; must never be 0.0.0.0/0."
  validation {
    condition     = !contains(var.allowed_cidrs, "0.0.0.0/0")
    error_message = "0.0.0.0/0 is not allowed; scope to known networks."
  }
}
