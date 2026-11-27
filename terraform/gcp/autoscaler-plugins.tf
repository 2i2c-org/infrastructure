# Service account for k8s-autoscaler-plugins https://github.com/2i2c-org/k8s-autoscaler-plugins
# resource ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_service_account_iam
resource "google_service_account" "autoscaler_plugins_sa" {
  count        = var.enable_k8s_autoscaler_plugins ? 1 : 0
  account_id   = "${var.prefix}-autoscaler-plugins"
  display_name = "Service account for k8s-autoscaler-plugins with GKE Cluster Admin role for cluster ${var.prefix}"
  project      = var.project_id
}

# Service account roles for k8s-autoscaler-plugins https://github.com/2i2c-org/k8s-autoscaler-plugins
# resource ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam#google_project_iam_member
resource "google_project_iam_member" "autoscaler_plugins_sa_roles" {
  count   = var.enable_k8s_autoscaler_plugins ? 1 : 0
  project = var.project_id
  role    = "roles/container.clusterAdmin"
  member  = "serviceAccount:${google_service_account.autoscaler_plugins_sa[count.index].email}"
}

resource "google_service_account_iam_binding" "autoscaler_plugins_sa_binding" {
  count              = var.enable_k8s_autoscaler_plugins ? 1 : 0
  service_account_id = google_service_account.autoscaler_plugins_sa[count.index].name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[support/support-k8s-autoscaler-plugins]"
  ]
}

output "autoscaler_plugins_k8s_sa_annotation" {
  value = var.enable_k8s_autoscaler_plugins ? "iam.gke.io/gcp-service-account: serviceAccount:${google_service_account.autoscaler_plugins_sa[0].email}" : null
}