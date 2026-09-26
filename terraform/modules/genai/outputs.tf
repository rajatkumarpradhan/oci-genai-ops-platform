output "cluster_id" {
  value = oci_generative_ai_dedicated_ai_cluster.this.id
}

output "endpoint_id" {
  value = oci_generative_ai_endpoint.chat.id
}
