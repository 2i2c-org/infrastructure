terraform {
  required_version = "~> 1.5"

  backend "gcs" {}
  required_providers {
    google = {
      # ref: https://registry.terraform.io/providers/hashicorp/google/latest
      source  = "google"
      version = "~> 4.55"
    }
    google-beta = {
      # ref: https://registry.terraform.io/providers/hashicorp/google-beta/latest
      source  = "google-beta"
      version = "~> 4.55"
    }
    kubernetes = {
      # ref: https://registry.terraform.io/providers/hashicorp/kubernetes/latest
      source  = "hashicorp/kubernetes"
      version = "~> 2.18"
    }
    # Used to decrypt sops encrypted secrets containing PagerDuty keys
    sops = {
      # ref: https://registry.terraform.io/providers/carlpett/sops/latest
      source  = "carlpett/sops"
      version = "~> 0.7.2"
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

