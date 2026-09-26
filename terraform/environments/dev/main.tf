terraform {
  required_version = ">= 1.6.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.region
}

module "genai" {
  source         = "../../modules/genai"
  compartment_id = var.compartment_id
  name_prefix    = "genaiops-dev"
  unit_count     = 1
  unit_shape     = "LLAMA2_70"
  model_id       = var.model_id
}

module "vector_db" {
  source         = "../../modules/vector_db"
  compartment_id = var.compartment_id
  name_prefix    = "genaiops-dev"
  is_free_tier   = true
  admin_password = var.adb_admin_password
  allowed_cidrs  = var.allowed_cidrs
}

module "observability" {
  source         = "../../modules/observability"
  compartment_id = var.compartment_id
  name_prefix    = "genaiops-dev"
  alert_email    = var.alert_email
  monthly_budget = 100
}
