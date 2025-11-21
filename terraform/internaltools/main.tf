terraform {
  required_version = "~> 1.5"
  backend "gcs" {
    # This is a separate GCS bucket than what we use for our other terraform state
    bucket = "two-eye-two-see-internal-tools-tfstate"
    prefix = "terraform/state/internal-tools"
  }
  required_providers {
    google = {
      # FIXME: upgrade to v6, see https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/version_6_upgrade
      # ref: https://registry.terraform.io/providers/hashicorp/google/latest
      source  = "google"
      version = "~> 5.43"
    }

    sops = {
      source  = "carlpett/sops"
      version = "~> 1.1"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "3.1.1"
    }

    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.38.0"
    }
  }
}
