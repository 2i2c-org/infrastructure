/**
* This file defines alerts and notification channels for sending information to
* PagerDuty in order to trigger incidents. This relies on pre-registered
* PagerDuty services with "stackdriver" integrations in 2i2c's PagerDuty
* account.
*
* - PagerDuty services in 2i2c's PagerDuty account:
*   https://2i2c-org.pagerduty.com/service-directory/?direction=asc&query=&team_ids=all
* - GCP docs about managing notification channels:
*   https://cloud.google.com/monitoring/support/notification-options
*
*/
data "sops_file" "pagerduty_service_integration_keys" {
  # Read sops encrypted file containing integration key for pagerduty
  source_file = "secret/enc-pagerduty-service-integration-keys.secret.yaml"
}

resource "google_monitoring_notification_channel" "pagerduty_disk_space" {
  project      = var.project_id
  display_name = "PagerDuty Disk Space Alerts"
  type         = "pagerduty"
  sensitive_labels {
    service_key = data.sops_file.pagerduty_service_integration_keys.data["pagerduty_service_integration_keys.disk_space"]
  }
}

resource "google_monitoring_alert_policy" "disk_space_full_alert" {

  display_name = "Disk Space 80% full on ${var.project_id}"
  combiner     = "OR"

  conditions {
    display_name = "Simple Health Check Endpoint"
    condition_threshold {
      # Alert based on free bytes left on the filesystem
      filter   = <<-EOT
      resource.type = "filestore_instance"
      AND metric.type = "file.googleapis.com/nfs/server/free_bytes"
      EOT
      duration = "300s"

      # Trigger if free space is < 512GB
      threshold_value = 549755813888
      comparison      = "COMPARISON_LT"

      aggregations {
        # https://cloud.google.com/monitoring/alerts/concepts-indepth#duration has
        # more info on alignment
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_NONE"
      }
    }
  }

  project = var.project_id

  # Send a notification to our PagerDuty channel when this is triggered
  notification_channels = [google_monitoring_notification_channel.pagerduty_disk_space.name]
}
