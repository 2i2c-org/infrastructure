# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
resource "aws_s3_bucket" "user_buckets" {
  for_each = var.user_buckets
  bucket   = lower("${var.cluster_name}-${each.key}")
  tags     = each.value.tags
}

# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration
resource "aws_s3_bucket_lifecycle_configuration" "user_bucket_expiry" {
  for_each = var.user_buckets
  bucket   = lower("${var.cluster_name}-${each.key}")

  rule {
    id     = "delete-after-expiry"
    status = each.value.delete_after != null ? "Enabled" : "Disabled"

    expiration {
      days = each.value.delete_after
    }

    filter {
      prefix = ""
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

locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  bucket_permissions = distinct(flatten([
    for hub_name, permissions in var.hub_cloud_permissions : [
      for bucket_name in permissions.bucket_admin_access : {
        hub_name    = hub_name
        bucket_name = bucket_name
      }
    ]
  ]))
}

# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document
data "aws_iam_policy_document" "bucket_access" {
  for_each = { for bp in local.bucket_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  statement {
    effect  = "Allow"
    actions = ["s3:*"]
    principals {
      type = "AWS"
      identifiers = [
        aws_iam_role.irsa_role[each.value.hub_name].arn
      ]
    }
    resources = [
      # Grant access only to the bucket and its contents
      aws_s3_bucket.user_buckets[each.value.bucket_name].arn,
      "${aws_s3_bucket.user_buckets[each.value.bucket_name].arn}/*"
    ]
  }
}

# There can only be one of these per bucket, if more are defined they will end
# up replacing each other without terraform indicating there is trouble.
#
# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy
resource "aws_s3_bucket_policy" "user_bucket_access" {
  for_each = { for bp in local.bucket_permissions : "${bp.hub_name}.${bp.bucket_name}" => bp }
  bucket   = aws_s3_bucket.user_buckets[each.value.bucket_name].id
  policy   = data.aws_iam_policy_document.bucket_access[each.key].json
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
