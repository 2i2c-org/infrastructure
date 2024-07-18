# Set up a Workload Identity and Google Service Account (with appropriate
# permissions) with a binding to a Kubernetes Service Account to perform backups
# of the Filestore.

# Create the service account if we are enabling filestore backups
resource "google_service_account" "filestore_backup_sa" {
  count = var.enable_filestore_backups ? 1 : 0
  # Service account IDs are limited to 30 chars
  account_id   = "${var.prefix}-filestore-backup"
  display_name = "Service account for gcp-filestore-backups pods in ${var.prefix}"
  project      = var.project_id
}

# To manage backups of the GCP Filestore, the calling code needs to have
# file.backups.* permission. We create a role granting just this to provide the
# filestore backup SA, so pods can use it.
resource "google_project_iam_custom_role" "filestore_backups" {
  count = var.enable_filestore_backups ? 1 : 0
  // Role names can't contain -, so we swap them out. BOO
  role_id     = replace("${var.prefix}_filestore_backups", "-", "_")
  project     = var.project_id
  title       = "Identify as project role for pods in ${var.prefix}"
  description = "Minimal role for gcp-filestore-backups pods on ${var.prefix} to identify as current project"
  permissions = ["file.backups.*"]
}

resource "google_project_iam_member" "filestore_backups_binding" {
  count    = var.enable_filestore_backups ? 1 : 0
  project  = var.project_id
  role     = google_project_iam_custom_role.filestore_backups[0].name
  member   = "serviceAccount:${google_service_account.filestore_backup_sa[0].email}"
}

# Bind the Kubernetes Service Accounts to their appropriate Google Cloud Service Accounts
resource "google_service_account_iam_binding" "filestore_backups_binding" {
  count              = var.enable_filestore_backups ? 1 : 0
  service_account_id = google_service_account.filestore_backup_sa[0].id
  role               = "roles/iam.workloadIdentityUser"
  # This will be deployed into the support namespace
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[support/gcp-filestore-backups-sa]"
  ]
}

output "gcp_filestore_backups_k8s_sa_annotations" {
  value       = var.enable_filestore_backups ? "iam.gke.io/gcp-service-account: ${google_service_account.filestore_backup_sa[0].email}" : ""
  description = <<-EOT
  Annotations to apply to gcpFilestoreBackups in the support chart to enable cloud permissions for its pods.

  This should be specified under gcpFilestoreBackups.annotations in a support
  values file created for the cluster.
  EOT
}