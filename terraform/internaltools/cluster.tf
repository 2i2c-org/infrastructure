resource "google_container_cluster" "internaltools" {
  name     = "internaltools"
  location = "us-central1-b"
  project  = var.project_id

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection      = false
}

resource "google_container_node_pool" "main" {
  name       = "main"
  location   = "us-central1-b"
  cluster    = google_container_cluster.internaltools.name
  node_count = 1
  project    = var.project_id

  node_config {
    machine_type = "e2-medium"
  }
}

data "google_client_config" "current" {}

provider "helm" {
  kubernetes = {
    host  = "https://${google_container_cluster.internaltools.endpoint}"
    token = data.google_client_config.current.access_token
    cluster_ca_certificate = base64decode(
      google_container_cluster.internaltools.master_auth[0].cluster_ca_certificate,
    )
    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "gke-gcloud-auth-plugin"
    }
  }
}

provider "kubernetes" {
  host  = "https://${google_container_cluster.internaltools.endpoint}"
  token = data.google_client_config.current.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.internaltools.master_auth[0].cluster_ca_certificate,
  )
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "gke-gcloud-auth-plugin"
  }

}