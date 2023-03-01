terraform {
  backend "gcs" {
    # This is a separate GCS bucket than what we use for our other terraform state
    # This is less sensitive, so let's keep it separate
    bucket = "two-eye-two-see-uptime-checks-tfstate"
    prefix = "terraform/state/uptime-checks"
  }
  required_providers {
    google = {
      # ref: https://registry.terraform.io/providers/hashicorp/google/latest
      source  = "google"
      version = "~> 4.55"
    }

    # Used to decrypt sops encrypted secrets containing PagerDuty keys
    sops = {
      # ref: https://registry.terraform.io/providers/carlpett/sops/latest
      source  = "carlpett/sops"
      version = "~> 0.7.2"
    }
  }
}
