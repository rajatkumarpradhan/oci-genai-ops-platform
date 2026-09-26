output "alerts_topic_id" {
  value = oci_ons_notification_topic.alerts.id
}

output "budget_id" {
  value = oci_budget_budget.monthly.id
}

output "log_group_id" {
  value = oci_logging_log_group.platform.id
}

output "budget_alert_type" {
  value = oci_budget_alert_rule.forecast_80.type
}

output "alarm_enabled" {
  value = oci_monitoring_alarm.endpoint_errors.is_enabled
}
