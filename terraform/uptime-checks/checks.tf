# Setup local variables with list of hubs that we want checks for
locals {
  cluster_yamls = [for f in fileset(path.module, "../../config/clusters/*/cluster.yaml") : yamldecode(file(f))]
  hubs = toset(flatten([for cy in local.cluster_yamls : [for h in cy["hubs"] : {
    name       = h["name"],
    domain     = h["domain"]
    helm_chart = h["helm_chart"]
    cluster    = cy["name"]
    provider   = cy["provider"]
  }]]))
  # A list of all prometheus servers
  prometheuses = flatten([
    for cy in local.cluster_yamls : [
      for f in cy["support"]["helm_chart_values_files"] : {
        # Requires the directory of the cluster file matches the cluster name
        "domain" : yamldecode(file("../../config/clusters/${cy.name}/${f}"))["prometheus"]["server"]["ingress"]["hosts"][0],
        "cluster" : cy["name"]
      } if !startswith(f, "enc-")
    ]
  ])
}

resource "google_monitoring_uptime_check_config" "hub_simple_uptime_check" {
  for_each = { for h in local.hubs : h.domain => h }

  display_name = "${each.value.domain} on ${each.value.cluster}"
  timeout      = "30s"

  # Check every 15 minutes
  period = "900s"
  selected_regions = ["USA"]

  http_check {
    # BinderHub has a different health check URL
    path           = each.value.helm_chart != "binderhub" ? "/hub/health" : "/health"
    port           = 443
    use_ssl        = true
    request_method = "GET"
    accepted_response_status_codes {
      # 200 is the only acceptable status code
      status_value = "200"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      # This specifies the project within which the *check* exists, not where the hub exists
      project_id = var.project_id
      # This specifies the domain to check
      host = each.value.domain
    }
  }

  project = var.project_id
}

resource "google_monitoring_alert_policy" "hub_simple_uptime_alert" {
  for_each = { for h in local.hubs : h.domain => h }

  display_name = "${each.value.domain} on ${each.value.cluster}"
  combiner     = "OR"

  conditions {
    display_name = "Simple Health Check Endpoint"
    condition_threshold {
      filter = <<-EOT
      resource.type = "uptime_url"
      AND metric.type = "monitoring.googleapis.com/uptime_check/check_passed"
      AND metric.labels.check_id = "${google_monitoring_uptime_check_config.hub_simple_uptime_check[each.key].uptime_check_id}"
      EOT
      # Alert if we have a failure condition for 31 minutes - given we do checks
      # every 15 minutes, this means we alert if two checks have failed. This shoulod
      # prevent alerts if the hub is momentarily down during a deployment. All alerts
      # *must* be actionable, so we trade-off some latency here for resiliency.
      duration        = "1860s"
      threshold_value = 1 # 1 means 'a check failed', 0 means 'a check succeeded'
      comparison      = "COMPARISON_GT"
      aggregations {
        group_by_fields = ["resource.label.host"]
        # https://cloud.google.com/monitoring/alerts/concepts-indepth#duration has
        # more info on alignment
        alignment_period   = "900s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
        # Count each failure as a "1"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
      }
    }
  }

  project = var.project_id

  # Send a notification to our PagerDuty channel when this is triggered
  notification_channels = [google_monitoring_notification_channel.pagerduty_hubs.name]
}

resource "google_monitoring_uptime_check_config" "prometheus_simple_uptime_check" {
  for_each = { for p in local.prometheuses : p.domain => p }

  display_name = "${each.value.domain} on ${each.value.cluster}"
  timeout      = "30s"

  # Check every 15 minutes
  period = "900s"
  selected_regions = ["USA"]

  http_check {
    path           = "/"
    port           = 443
    use_ssl        = true
    request_method = "GET"
    accepted_response_status_codes {
      # We just wanna check if this prometheus is running, let's not try authenticate to it
      status_value = "401"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      # This specifies the project within which the *check* exists, not where the hub exists
      project_id = var.project_id
      # This specifies the domain to check
      host = each.value.domain
    }
  }

  project = var.project_id
}

resource "google_monitoring_alert_policy" "prometheus_simple_uptime_alert" {
  for_each = { for p in local.prometheuses : p.domain => p }

  display_name = "${each.value.domain} on ${each.value.cluster}"
  combiner     = "OR"

  conditions {
    display_name = "Simple Prometheus Health Check Endpoint"
    condition_threshold {
      filter = <<-EOT
      resource.type = "uptime_url"
      AND metric.type = "monitoring.googleapis.com/uptime_check/check_passed"
      AND metric.labels.check_id = "${google_monitoring_uptime_check_config.prometheus_simple_uptime_check[each.key].uptime_check_id}"
      EOT
      # Alert if we have a failure condition for 31 minutes - given we do checks
      # every 15 minutes, this means we alert if two checks have failed. This shoulod
      # prevent alerts if the hub is momentarily down during a deployment. All alerts
      # *must* be actionable, so we trade-off some latency here for resiliency.
      duration        = "1860s"
      threshold_value = 1 # 1 means 'a check failed', 0 means 'a check succeeded'
      comparison      = "COMPARISON_GT"
      aggregations {
        group_by_fields = ["resource.label.host"]
        # https://cloud.google.com/monitoring/alerts/concepts-indepth#duration has
        # more info on alignment
        alignment_period   = "900s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
        # Count each failure as a "1"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
      }
    }
  }

  project = var.project_id

  # Send a notification to our PagerDuty channel when this is triggered
  notification_channels = [google_monitoring_notification_channel.pagerduty_prometheus.name]
}
