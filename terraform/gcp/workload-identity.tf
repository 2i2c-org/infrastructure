# User pods need to authenticate to cloud APIs - particularly around storage.
# On GKE, Workload Identity (https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
# is the canonical way to do this securely. A Google Cloud Service Account (GSA)
# is created and given appropriate rights, and then bound to a Kubernetes Service Account (KSA)
# via workload identity. All pods that then mount this kubernetes service account (named user-sa)
# get the cloud permissions assigned to the Google Cloud Service Account.
#
# Since each cluster can contain multiple hubs, we need to tell terraform which hubs we want
# to equip with the KSA that has cloud credentials. Terraform will create this Kubernetes
# Service Account (and the namespace, if it does not exist). We will also need to tell it
# exactly what permissions we want each hub to have, so we don't give them too many
# permissions

# Create the service account if there is an entry for the hub, regardless of what
# kind of permissions it wants.
resource "google_service_account" "workload_sa" {
  for_each     = var.hub_cloud_permissions
  account_id   = "${var.prefix}-${each.key}"
  display_name = "Service account for user pods in hub ${each.key} in ${var.prefix}"
  project      = var.project_id
}


# Bind the Kubernetes Service Accounts to their appropriate Google Cloud Service Accounts
resource "google_service_account_iam_binding" "workload_identity_binding" {
  for_each           = var.hub_cloud_permissions
  service_account_id = google_service_account.workload_sa[each.key].id
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${each.value.hub_namespace}/user-sa]"
  ]
}

# To access GCS buckets with requestor pays, the calling code needs
# to have serviceusage.services.use permission. We create a role
# granting just this to provide the workload SA, so user pods can
# use it. See https://cloud.google.com/storage/docs/requester-pays
# for more info
resource "google_project_iam_custom_role" "requestor_pays" {
  // Role names can't contain -, so we swap them out. BOO
  role_id     = replace("${var.prefix}_requestor_pays", "-", "_")
  project     = var.project_id
  title       = "Identify as project role for users in ${var.prefix}"
  description = "Minimal role for hub users on ${var.prefix} to identify as current project"
  permissions = ["serviceusage.services.use"]
}

resource "google_project_iam_member" "requestor_pays_binding" {
  for_each = toset([for hub_name, permissions in var.hub_cloud_permissions : hub_name if permissions.requestor_pays])
  project  = var.project_id
  role     = google_project_iam_custom_role.requestor_pays.name
  member   = "serviceAccount:${google_service_account.workload_sa[each.value].email}"
}

# Create the Service Account in the Kubernetes Namespace
# FIXME: We might need to create the k8s namespace here some of the time, but then who is
# responsible for that - terraform or helm (via our deployer?)
resource "kubernetes_service_account" "workload_kubernetes_sa" {
  for_each = var.hub_cloud_permissions

  metadata {
    name      = "user-sa"
    namespace = each.value.hub_namespace
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.workload_sa[each.key].email
    }
  }
}
