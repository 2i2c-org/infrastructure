terraform {
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

// Service account used by all the nodes and pods in our cluster
resource "google_service_account" "cluster_sa" {
  account_id   = "${var.prefix}-cluster-sa"
  display_name = "Cluster SA for ${var.prefix}"
  project      = var.project_id
}

// To access GCS buckets with requestor pays, the calling code needs
// to have serviceusage.services.use permission. We create a role
// granting just this to provide the cluster SA, so user pods can
// use it. See https://cloud.google.com/storage/docs/requester-pays
// for more info
resource "google_project_iam_custom_role" "identify_project_role" {
  // Role names can't contain -, so we swap them out. BOO
  role_id     = replace("${var.prefix}_user_sa_role", "-", "_")
  project     = var.project_id
  title       = "Identify as project role for users in ${var.prefix}"
  description = "Minimal role for hub users on ${var.prefix} to identify as current project"
  permissions = ["serviceusage.services.use"]
}

resource "google_project_iam_member" "identify_project_binding" {
  project = var.project_id
  role    = google_project_iam_custom_role.identify_project_role.name
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}

resource "google_project_iam_member" "cluster_sa_roles" {
  for_each = var.cluster_sa_roles

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}
