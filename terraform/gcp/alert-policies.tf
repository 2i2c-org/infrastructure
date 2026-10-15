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

resource "google_logging_metric" "scale_up_failed_oo_resources" {
  project = var.project_id
  name    = "scale-up-oo-resources"
  filter  = <<-EOT
  logName="projects/${var.project_id}/logs/container.googleapis.com%2Fcluster-autoscaler-visibility"
  (jsonPayload.resultInfo.results.errorMsg.messageId="scale.up.error.out.of.resources")
  EOT
  metric_descriptor {
    display_name = "Could not scale up nodegroup"
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    labels {
      key         = "zone"
      value_type  = "STRING"
      description = "Node zone"
    }
    labels {
      key         = "instance_group"
      value_type  = "STRING"
      description = "Instance group requested"
    }
  }
  label_extractors = {
    zone           = "REGEXP_EXTRACT(jsonPayload.resultInfo.results.errorMsg.parameters, \"zones/([^/]+)\")"
    instance_group = "REGEXP_EXTRACT(jsonPayload.resultInfo.results.errorMsg.parameters, \"instanceGroups/([^/]+)\")"
  }
}

resource "google_monitoring_alert_policy" "out_of_resources_alert" {
  display_name = "Resource exhaustion policy"
  project      = var.project_id
  combiner     = "OR"
  enabled      = true
  severity     = "CRITICAL"

  conditions {
    display_name = "Out Of Resources condition"

    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.scale_up_failed_oo_resources.name}\" AND resource.type=\"k8s_cluster\""
      comparison      = "COMPARISON_GT"
      threshold_value = "0"
      # Alert immediately we get the oor (out of resources) log message
      duration = "0s"

      aggregations {
        # Only alert once in 10min
        alignment_period   = "600s"
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }

  alert_strategy {
    # seven days
    auto_close = "604800s"
  }

  # Send a notification to our PagerDuty channel when this is triggered
  notification_channels = var.prefix == "cloudbank" ? [google_monitoring_notification_channel.pagerduty_cloudbank[0].name] : [
    google_monitoring_notification_channel.pagerduty_scaleup[0].name
  ]
}
