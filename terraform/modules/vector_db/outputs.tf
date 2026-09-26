output "adb_id" {
  value = oci_database_autonomous_database.vectors.id
}

output "connection_strings" {
  value     = oci_database_autonomous_database.vectors.connection_strings
  sensitive = true
}

output "whitelisted_ips" {
  value = oci_database_autonomous_database.vectors.whitelisted_ips
}
