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

  dynamic "lifecycle_rule" {
    for_each = each.value.delete_after != null ? [1] : []

    content {
      condition {
        age = each.value.delete_after
      }
      action {
        type = "Delete"
      }
    }

  }
}

locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  bucket_admin_permissions = distinct(flatten([
    for hub_name, permissions in var.hub_cloud_permissions : [
      for bucket_name in permissions.bucket_admin_access : {
        hub_name    = hub_name
        bucket_name = bucket_name
      }
    ]
  ]))

  bucket_readonly_permissions = distinct(flatten([
    for hub_name, permissions in var.hub_cloud_permissions : [
      for bucket_name in permissions.bucket_readonly_access : {
        hub_name    = hub_name
        bucket_name = bucket_name
      }
    ]
  ]))

  bucket_extra_admin_members = distinct(flatten([
    for bucket_name, properties in var.user_buckets : [
      for extra_member in properties.extra_admin_members : {
        bucket_name = bucket_name
        member      = extra_member
      }
    ]
  ]))

  bucket_public_permissions = distinct(flatten([
    for hub_name, permissions in var.hub_cloud_permissions : [
      for bucket_name in permissions.bucket_public_access : {
        hub_name    = hub_name
        bucket_name = bucket_name
      }
    ]
  ]))
}

resource "google_storage_bucket_iam_member" "member" {
  for_each = { for bp in local.bucket_admin_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  bucket   = google_storage_bucket.user_buckets[each.value.bucket_name].name
  role     = "roles/storage.admin"
  member   = "serviceAccount:${google_service_account.workload_sa[each.value.hub_name].email}"
}

resource "google_storage_bucket_iam_member" "member_readonly" {
  for_each = { for bp in local.bucket_readonly_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  bucket   = google_storage_bucket.user_buckets[each.value.bucket_name].name
  role     = "roles/storage.objectViewer"
  member   = "serviceAccount:${google_service_account.workload_sa[each.value.hub_name].email}"
}

resource "google_storage_bucket_iam_member" "extra_admin_members" {
  for_each = { for bm in local.bucket_extra_admin_members : "${bm.bucket_name}.${bm.member}" => bm }
  bucket   = google_storage_bucket.user_buckets[each.value.bucket_name].name
  role     = "roles/storage.admin"
  member   = each.value.member
}

resource "google_storage_bucket_access_control" "public_rule" {
  for_each = { for bp in local.bucket_public_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  bucket   = google_storage_bucket.user_buckets[each.value.bucket_name].name
  role     = "READER"
  entity   = "allUsers"
}

output "buckets" {
  value       = { for b, _ in var.user_buckets : b => google_storage_bucket.user_buckets[b].name }
  description = <<-EOT
  List of GCS buckets created for this cluster

  Since GCS bucket names need to be globally unique, we prefix each item in
  the user_buckets variable with the prefix variable. This output displays
  the full name of all GCS buckets created conveniently.
  EOT
}
