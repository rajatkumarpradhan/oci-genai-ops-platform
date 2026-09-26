variable "tenancy_ocid" {
  type = string
}

variable "region" {
  type    = string
  default = "ap-mumbai-1"
}

variable "compartment_id" {
  type = string
}

variable "model_id" {
  type        = string
  description = "Base model OCID for the hosted endpoint."
  default     = "ocid1.generativeaimodel.oc1..example"
}

variable "adb_admin_password" {
  type      = string
  sensitive = true
}

variable "allowed_cidrs" {
  type    = list(string)
  default = ["10.0.0.0/8"]
}

variable "alert_email" {
  type = string
}
