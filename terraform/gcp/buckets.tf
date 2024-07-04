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

  dynamic "logging" {
    for_each = each.value.usage_logs ? [1] : []

    content {
      log_bucket = google_storage_bucket.usage_logs_bucket[0].name
    }
  }

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

# Create GCS bucket that can store *usage* logs (access logs).
# Helpful to see what data is *actually* being used.
# https://cloud.google.com/storage/docs/access-logs
#
# We create this bucket unconditionally, because it costs nothing.
# It only costs if we actually enable this logging, which is done in
# per-bucket config.
#
# We only keep them for 30 days so they don't end up costing a
# ton of money
resource "google_storage_bucket" "usage_logs_bucket" {
  count    = var.enable_logging ? 1 : 0
  name     = "${var.prefix}-gcs-usage-logs"
  location = var.region
  project  = var.project_id

  labels = {}

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Provide access to GCS infrastructure to write usage logs to this bucket
resource "google_storage_bucket_iam_member" "usage_logs_bucket_access" {
  count  = var.enable_logging ? 1 : 0
  bucket = google_storage_bucket.usage_logs_bucket[0].name
  member = "group:cloud-storage-analytics@google.com"
  role   = "roles/storage.objectCreator"
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

resource "google_storage_bucket_iam_member" "public_access" {
  for_each = { for k, v in var.user_buckets : k => v if v.public_access }
  bucket   = google_storage_bucket.user_buckets[each.key].name
  role     = "roles/storage.objectViewer"
  member   = "allUsers"
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

output "usage_log_bucket" {
  value       = var.enable_logging ? google_storage_bucket.usage_logs_bucket[0].name : null
  description = <<-EOT
  Name of GCS bucket containing GCS usage logs (when enabled).

  https://cloud.google.com/storage/docs/access-logs has more information
  on GCS usage logs. It has to be enabled on a per-bucket basis - see
  the documentation for the `user_buckets` variable for more information.
  EOT
}