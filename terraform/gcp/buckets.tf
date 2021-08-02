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

resource "google_storage_bucket_iam_member" "member" {

  for_each = var.user_buckets
  bucket   = google_storage_bucket.user_buckets[each.key].name
  role     = "roles/storage.admin"
  member   = "serviceAccount:${google_service_account.cluster_sa.email}"
}
