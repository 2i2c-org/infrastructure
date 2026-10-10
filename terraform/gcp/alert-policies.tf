data "sops_file" "pagerduty_integration_key" {
  # Read sops encrypted file containing integration key for pagerduty
  source_file = "../uptime-checks/secret/enc-pagerduty-service-key.secret.yaml"
}

resource "google_monitoring_notification_channel" "pagerduty_scaleup" {
  count        = var.prefix == "cloudbank" ? 0 : 1
  project      = var.project_id
  display_name = "PagerDuty Scale Up Out Of Resources"
  type         = "pagerduty"
  sensitive_labels {
    service_key = data.sops_file.pagerduty_integration_key.data["pagerduty.scaleup"]
  }
}

resource "google_monitoring_notification_channel" "pagerduty_cloudbank" {
  count        = var.prefix == "cloudbank" ? 1 : 0
  project      = var.project_id
  display_name = "PagerDuty Cloudbank cluster alerts"
  type         = "pagerduty"
  sensitive_labels {
    service_key = data.sops_file.pagerduty_integration_key.data["pagerduty.cloudbank"]
  }
}

resource "google_monitoring_alert_policy" "cluster_autoscaler_out_of_resources_alert" {
  display_name = "Autoscaler out of resources"
  project      = var.project_id
  combiner     = "OR"
  enabled      = true
  severity     = "CRITICAL"
  conditions {
    display_name = "Scale Up Error Out Of Resources"
    condition_matched_log {
      filter = <<-EOT
      logName="projects/${var.project_id}/logs/container.googleapis.com%2Fcluster-autoscaler-visibility"
      (jsonPayload.resultInfo.results.errorMsg.messageId="scale.up.error.out.of.resources")
      EOT
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "3600s"
    }

    # seven days
    auto_close = "604800s"
  }

  # Send a notification to our PagerDuty channel when this is triggered
  notification_channels = var.prefix == "cloudbank" ? [google_monitoring_notification_channel.pagerduty_cloudbank[0].name] : [
    google_monitoring_notification_channel.pagerduty_scaleup[0].name
  ]
}
