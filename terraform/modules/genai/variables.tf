variable "compartment_id" {
  type        = string
  description = "Compartment OCID for GenAI resources."
}

variable "name_prefix" {
  type        = string
  description = "Prefix for display names."
  default     = "genaiops"
}

variable "unit_count" {
  type        = number
  description = "Dedicated AI cluster units."
  default     = 1
  validation {
    condition     = var.unit_count >= 1 && var.unit_count <= 10
    error_message = "unit_count must be between 1 and 10."
  }
}

variable "unit_shape" {
  type        = string
  description = "Cluster unit shape."
  default     = "LLAMA2_70"
}

variable "model_id" {
  type        = string
  description = "OCID of the base model to host on the endpoint."
}
