terraform {
  required_version = "~> 1.9"

  backend "gcs" {}
  required_providers {
    google = {
      # ref: https://registry.terraform.io/providers/hashicorp/google/latest
      source  = "google"
      version = "~> 5.36"
    }
    kubernetes = {
      # ref: https://registry.terraform.io/providers/hashicorp/kubernetes/latest
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"
    }
    # Used to decrypt sops encrypted secrets containing PagerDuty keys
    sops = {
      # ref: https://registry.terraform.io/providers/carlpett/sops/latest
      source  = "carlpett/sops"
      version = "~> 1.1"
    }
  }
}

provider "google" {
  user_project_override = true
  billing_project       = var.project_id
}

data "google_client_config" "default" {}

provider "kubernetes" {
  # From https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/guides/getting-started#provider-setup
  host  = "https://${google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
  )
}

