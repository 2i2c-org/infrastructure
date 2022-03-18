# User pods need to authenticate to cloud APIs - particularly around storage.
# On GKE, Workload Identity (https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
# is the canonical way to do this securely. A Google Cloud Service Account (GSA)
# is created and given appropriate rights, and then bound to a Kubernetes Service Account (KSA)
# via workload identity. All pods that then mount this kubernetes service account (named user-sa)
# get the cloud permissions assigned to the Google Cloud Service Account.
#
# Since each cluster can contain multiple hubs, we need to tell terraform which hubs we want
# to equip with the KSA that has cloud credentials. Terraform will create this Kubernetes
# Service Account (and the namespace, if it does not exist).

resource "google_service_account" "workload_sa" {
  for_each     = var.workload_identity_enabled_hubs
  account_id   = "${var.prefix}-${each.value}-workload-sa"
  display_name = "Service account for user pods in hub ${each.value} in ${var.prefix}"
  project      = var.project_id
}

# To access GCS buckets with requestor pays, the calling code needs
# to have serviceusage.services.use permission. We create a role
# granting just this to provide the workload SA, so user pods can
# use it. See https://cloud.google.com/storage/docs/requester-pays
# for more info
resource "google_project_iam_custom_role" "workload_role" {
  // Role names can't contain -, so we swap them out. BOO
  role_id     = replace("${var.prefix}_workload_sa_role", "-", "_")
  project     = var.project_id
  title       = "Identify as project role for users in ${var.prefix}"
  description = "Minimal role for hub users on ${var.prefix} to identify as current project"
  permissions = ["serviceusage.services.use"]
}

resource "google_project_iam_member" "workload_binding" {
  for_each = var.workload_identity_enabled_hubs
  project  = var.project_id
  role     = google_project_iam_custom_role.workload_role.name
  member   = "serviceAccount:${google_service_account.workload_sa[each.value].email}"
}

# Bind the Kubernetes Service Accounts to their appropriate Google Cloud Service Accounts
resource "google_service_account_iam_binding" "workload_identity_binding" {
  for_each           = var.workload_identity_enabled_hubs
  service_account_id = google_service_account.workload_sa[each.value].id
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${each.value}/user-sa]"
  ]
}

# Create the Service Account in the Kubernetes Namespace
# FIXME: We might need to create the k8s namespace here some of the time, but then who is
# responsible for that - terraform or helm (via our deployer?)
resource "kubernetes_service_account" "workload_kubernetes_sa" {
  for_each = var.workload_identity_enabled_hubs

  metadata {
    name      = "user-sa"
    namespace = each.value
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.workload_sa[each.value].email
    }
  }
}
