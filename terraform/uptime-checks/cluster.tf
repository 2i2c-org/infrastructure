resource "google_container_cluster" "sharedservices" {
  name     = "sharedservices"
  location = "us-central1-b"
  project = var.project_id

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection = false
}

resource "google_container_node_pool" "main" {
  name       = "main"
  location   = "us-central1-b"
  cluster    = google_container_cluster.sharedservices.name
  node_count = 1
  project = var.project_id

  node_config {
    machine_type = "e2-medium"
  }
}
