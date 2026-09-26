# Monitoring, logging and budget guardrails for the platform.
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

resource "oci_ons_notification_topic" "alerts" {
  compartment_id = var.compartment_id
  name           = "${var.name_prefix}-alerts"
}

resource "oci_ons_subscription" "email" {
  compartment_id = var.compartment_id
  topic_id       = oci_ons_notification_topic.alerts.id
  protocol       = "EMAIL"
  endpoint       = var.alert_email
}

resource "oci_monitoring_alarm" "endpoint_errors" {
  compartment_id        = var.compartment_id
  display_name          = "${var.name_prefix}-genai-endpoint-errors"
  metric_compartment_id = var.compartment_id
  namespace             = "oci_generative_ai_inference"
  query                 = "ErrorCount[5m].sum() > 10"
  severity              = "CRITICAL"
  destinations          = [oci_ons_notification_topic.alerts.id]
  is_enabled            = true
}

resource "oci_logging_log_group" "platform" {
  compartment_id = var.compartment_id
  display_name   = "${var.name_prefix}-logs"
}

resource "oci_budget_budget" "monthly" {
  compartment_id = var.compartment_id
  amount         = var.monthly_budget
  reset_period   = "MONTHLY"
  target_type    = "COMPARTMENT"
  targets        = [var.compartment_id]
}

resource "oci_budget_alert_rule" "forecast_80" {
  budget_id      = oci_budget_budget.monthly.id
  threshold      = 80
  threshold_type = "PERCENTAGE"
  type           = "FORECAST"
  recipients     = var.alert_email
}
