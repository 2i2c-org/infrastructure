variable "project_id" {
  type        = string
  default     = "two-eye-two-see"
  description = <<-EOT
  GCP project id containing all our uptime checks
  EOT
}

variable "federated_metrics_allowlist" {
  type = set(object({
    name         = string
    metric_regex = string
    labels_regex = string
  }))
  default = [
    {
      name         = "active-users"
      metric_regex = "jupyterhub_active_users"
      labels_regex = "period|namespace"
    },
    {
      name         = "pod-annotations"
      metric_regex = "kube_pod_annotations"
      labels_regex = "annotation_hub_jupyter_org_username|pod|namespace"
    }
  ]
  description = <<-EOT
  List of metrics to scrape and keep from all our community prometheus instances

  Each item is an object with two keys:
  1. metric_regex: Metrics matching this regex will be kept
  2. labels_regex: Labels matching this regex for this set of metrics matched by metric_regex will be kept

  Everything else will be discarded.
  EOT
}

variable "prometheus_namespace" {
  type        = string
  default     = "federated-prometheus"
  description = <<-EOT
  Namespace containing our federated prometheus install
  EOT
}

variable "prometheus_disk_size" {
  type        = number
  default     = 100
  description = "Size of the federated prometheus disk (in GiB)"
}