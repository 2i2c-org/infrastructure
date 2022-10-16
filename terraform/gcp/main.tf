terraform {
  backend "gcs" {}
  required_providers {
    google = {
      source  = "google"
      version = "4.40.0"
    }
    google-beta = {
      source  = "google-beta"
      version = "4.40.0"
    }
    kubernetes = {
      version = "2.8.0"
    }
  }
}

provider "google" {
  # This is required for Billing Alerts to work
  # See warning in https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/billing_budget
  user_project_override = true
  billing_project       = var.project_id
}
data "google_client_config" "default" {}

provider "kubernetes" {
  # From https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/guides/getting-started#provider-setup
  host  = "https://${google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.cluster.master_auth.0.cluster_ca_certificate
  )
}

