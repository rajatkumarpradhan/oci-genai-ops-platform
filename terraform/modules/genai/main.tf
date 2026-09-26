# OCI Generative AI dedicated cluster + endpoint (declared, not applied).
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

resource "oci_generative_ai_dedicated_ai_cluster" "this" {
  compartment_id = var.compartment_id
  display_name   = "${var.name_prefix}-genai-cluster"
  type           = "HOSTING"
  unit_count     = var.unit_count
  unit_shape     = var.unit_shape
}

resource "oci_generative_ai_endpoint" "chat" {
  compartment_id          = var.compartment_id
  dedicated_ai_cluster_id = oci_generative_ai_dedicated_ai_cluster.this.id
  display_name            = "${var.name_prefix}-chat-endpoint"
  model_id                = var.model_id
  content_moderation_config {
    is_enabled = true
  }
}
