/**
* GCS buckets for use by hub users
*/

resource "google_storage_bucket" "user_buckets" {
  for_each = var.user_buckets
  name     = "${var.prefix}-${each.key}"
  location = var.region
  project  = var.project_id

  // Set these values explicitly so they don't "change outside terraform"
  labels = {}
}

locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  bucket_permissions = distinct(flatten([
    for hub_name in var.workload_identity_enabled_hubs : [
      for bucket_name in var.user_buckets : {
        hub_name    = hub_name
        bucket_name = bucket_name
      }
    ]
  ]))
}

resource "google_storage_bucket_iam_member" "member" {
  for_each = { for bp in local.bucket_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  bucket   = google_storage_bucket.user_buckets[each.value.bucket_name].name
  role     = "roles/storage.admin"
  member   = "serviceAccount:${google_service_account.workload_sa[each.value.hub_name].email}"
}
