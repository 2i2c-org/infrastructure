/**
* Artifact Registry to store user images for this cluster.
*
* Hosting it in the same project makes node startup time faster.
*/
resource "google_artifact_registry_repository" "registry" {
  provider = google-beta

  location      = var.region
  repository_id = "${var.prefix}-registry"
  format        = "DOCKER"
  project       = var.project_id

  // Set these values explicitly so they don't "change outside terraform"
  labels = {}
}
