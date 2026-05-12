# Service account for Grafana, so it can access Google Cloud Stackdriver
resource "google_service_account" "grafana_sa" {
  account_id   = "grafana-2i2c-sa"
  display_name = "Service account for Grafana run by 2i2c"
  project      = var.project_id
}

resource "google_service_account_iam_binding" "grafana_sa_binding" {
  service_account_id = google_service_account.grafana_sa.id
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[support/support-grafana]"
  ]
}

resource "google_project_iam_member" "grafana_sa_membership" {
  project  = var.project_id
  role     = "roles/monitoring.viewer"
  member   = "serviceAccount:${google_service_account.grafana_sa.email}"
}
