# Autonomous Database for vector storage (Oracle 23ai AI Vector Search).
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

resource "oci_database_autonomous_database" "vectors" {
  compartment_id              = var.compartment_id
  display_name                = "${var.name_prefix}-vector-adb"
  db_name                     = var.db_name
  db_workload                 = "OLTP"
  db_version                  = "23ai"
  cpu_core_count              = 1
  data_storage_size_in_tbs    = 1
  is_free_tier                = var.is_free_tier
  admin_password              = var.admin_password
  whitelisted_ips             = var.allowed_cidrs
  is_mtls_connection_required = true
}
