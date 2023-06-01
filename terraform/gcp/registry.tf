/**
* Artifact Registry to store user images for this cluster.
*
* Hosting it in the same project makes node startup time faster.
*/
resource "google_artifact_registry_repository" "registry" {
  provider = google-beta

  for_each = toset(var.container_repos)

  location      = var.region
  repository_id = "${each.key}-registry"
  format        = "DOCKER"
  project       = var.project_id

  // Set these values explicitly so they don't "change outside terraform"
  labels = {}
}

// Create a service account for the hub to authenticate push/pulls to the GAR with
resource "google_service_account" "registry_sa" {
  for_each = toset(var.container_repos)

  account_id   = "${each.key}-registry-sa"
  display_name = "Service account to manage images in GAR repo ${each.key}"
  project      = var.project_id
}

// Assign the artifactregistry.writer role to the service account so that new images
// can be created and pushed
resource "google_project_iam_member" "registry_sa_roles" {
  for_each = google_service_account.registry_sa

  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${each.value.email}"
}

// Generate a key for each service account
resource "google_service_account_key" "registry_sa_keys" {
  for_each = google_service_account.registry_sa

  service_account_id = each.value.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

// Output the service account key for use in the hub config to authenticate image push/pulls
output "registry_sa_keys" {
  value     = { for cr in var.container_repos : cr => base64decode(google_service_account_key.registry_sa_keys[cr].private_key) }
  sensitive = true

  description = <<-EOT
  List of artifact registry service accounts created for this cluster.

  This output displays the private keys of each service account which can be supplied to
  hub config in order to authenticate the push/pull of images from the registry.
  EOT
}
