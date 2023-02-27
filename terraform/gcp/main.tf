terraform {
  backend "gcs" {}
  required_providers {
    google = {
      source  = "google"
      version = "4.51.0"
    }
    google-beta = {
      source  = "google-beta"
      version = "4.51.0"
    }
    kubernetes = {
      version = "2.8.0"
    }
  }
}

provider "google" {
  # This was configured without full understanding of the implications to
  # resolve the following error:
  #
  # Error: Error when reading or editing BillingBudget "...": googleapi: Error 403: Your application has authenticated using end user credentials from the Google Cloud SDK or Google Cloud Shell which are not supported by the billingbudgets.googleapis.com. We recommend configuring the billing/quota_project setting in gcloud or using a service account through the auth/impersonate_service_account setting. For more information about service accounts and how to use them in your application, see https://cloud.google.com/docs/authentication/. If you are getting this error with curl or similar tools, you may need to specify 'X-Goog-User-Project' HTTP header for quota and billing purposes. For more information regarding 'X-Goog-User-Project' header, please check https://cloud.google.com/apis/docs/system-parameters.
  #
  # Configuration reference:
  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#user_project_override
  #
  user_project_override = true
  billing_project = "two-eye-two-see"
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

