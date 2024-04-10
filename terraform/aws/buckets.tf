resource "aws_s3_bucket" "user_buckets" {
  for_each = var.user_buckets
  bucket   = lower("${var.cluster_name}-${each.key}")
}

resource "aws_s3_bucket_lifecycle_configuration" "user_bucket_expiry" {
  for_each = var.user_buckets
  bucket   = lower("${var.cluster_name}-${each.key}")

  rule {
    id     = "delete-after-expiry"
    status = each.value.delete_after != null ? "Enabled" : "Disabled"

    expiration {
      days = each.value.delete_after
    }
  }

  dynamic "rule" {
    # Only set up this rule if it will be enabled. Prevents unnecessary
    # churn in terraform
    for_each = each.value.archival_storageclass_after != null ? [1] : []

    content {
      id     = "archival-storageclass"
      status = "Enabled"

      transition {
        # Transition this to much cheaper object storage after a few days
        days = each.value.archival_storageclass_after
        # Glacier Instant is fast enough while also being pretty cheap
        storage_class = "GLACIER_IR"
      }
    }
  }
}

output "buckets" {
  value       = { for b, _ in var.user_buckets : b => aws_s3_bucket.user_buckets[b].id }
  description = <<-EOT
  List of S3 buckets created for this cluster

  Since S3 bucket names need to be globally unique, we prefix each item in
  the user_buckets variable with the prefix variable. This output displays
  the full name of all S3 buckets created conveniently.
  EOT
}
