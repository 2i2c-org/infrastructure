/**
* Setup Service Accounts for authentication during continuous deployment
*/

// Service account used by GitHub Actions to deploy to the cluster
resource "google_service_account" "cd_sa" {
  account_id   = "${var.prefix}-cd-sa"
  display_name = "Continuous Deployment SA for ${var.prefix}"
  project      = var.project_id
}

// Roles the service account needs to deploy hubs to the cluster
resource "google_project_iam_member" "cd_sa_roles" {
  for_each = var.cd_sa_roles

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cd_sa.email}"
}

// JSON encoded private key to be kept in secrets/* to for the
// deployment script to authenticate to the cluster
resource "google_service_account_key" "cd_sa" {
  service_account_id = google_service_account.cd_sa.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

output "ci_deployer_key" {
  value     = base64decode(google_service_account_key.cd_sa.private_key)
  sensitive = true
}
