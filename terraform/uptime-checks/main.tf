terraform {
  required_version = "~> 1.5"
  backend "gcs" {
    # This is a separate GCS bucket than what we use for our other terraform state
    # This is less sensitive, so let's keep it separate
    bucket = "two-eye-two-see-uptime-checks-tfstate"
    prefix = "terraform/state/uptime-checks"
  }
  required_providers {
    google = {
      # FIXME: upgrade to v6, see https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/version_6_upgrade
      # ref: https://registry.terraform.io/providers/hashicorp/google/latest
      source  = "google"
      version = "~> 5.43"
    }

    # Used to decrypt sops encrypted secrets containing PagerDuty keys
    sops = {
      # ref: https://registry.terraform.io/providers/carlpett/sops/latest
      source  = "carlpett/sops"
      version = "~> 1.1"
    }
  }
}
