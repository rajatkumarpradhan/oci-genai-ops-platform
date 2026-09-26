# Unit tests with a fully mocked OCI provider: no tenancy, credentials or spend.
mock_provider "oci" {}

variables {
  tenancy_ocid       = "ocid1.tenancy.oc1..test"
  compartment_id     = "ocid1.tenancy.oc1..test"
  alert_email        = "alerts@example.com"
  adb_admin_password = "TestOnly-NotARealPassword1"
  allowed_cidrs      = ["10.0.0.0/8"]
}

run "budget_guardrail_is_forecast_based" {
  command = plan

  assert {
    condition     = module.observability.budget_alert_type == "FORECAST"
    error_message = "The 80% budget alert must trigger on forecast, not only on actual spend."
  }
}

run "adb_never_open_to_the_world" {
  command = plan

  assert {
    condition     = !contains(module.vector_db.whitelisted_ips, "0.0.0.0/0")
    error_message = "The vector database must never allow 0.0.0.0/0."
  }
}

run "alarms_are_enabled" {
  command = plan

  assert {
    condition     = module.observability.alarm_enabled == true
    error_message = "The GenAI endpoint error alarm must be enabled."
  }
}
