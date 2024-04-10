locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  hub_role_bucket = flatten([
    for hub, hub_value in var.hub_cloud_permissions : [
      for role, role_value in hub_value : flatten([
        [
          for bucket in role_value.bucket_admin_access : {
            // id can be simplified, it was set to not change anything
            id = role == "user-sa" ? "${hub}.${bucket}" : "${hub}.${role}.${bucket}.admin"
            // role should match the id set in irsa.tf
            role    = role == "user-sa" ? hub : "${hub}-${role}"
            bucket  = bucket
            actions = ["s3:*"]
          }
        ],
        [
          for bucket in role_value.bucket_readonly_access : {
            id = "${hub}.${role}.${bucket}.readonly"
            // role should match the id set in irsa.tf
            role   = role == "user-sa" ? hub : "${hub}-${role}"
            bucket = bucket
            actions = [
              "s3:ListBucket",
              "s3:GetObject",
              "s3:GetObjectVersion",
            ]
          }
        ]
      ])
    ]
  ])
}

// FIXME: there can only be one declared per bucket, so if we have multiple
//        roles that has permissions, we need to merge them
data "aws_iam_policy_document" "bucket_admin_access" {
  for_each = { for index, hrb in local.hub_role_bucket : hrb.id => hrb }
  statement {
    effect  = "Allow"
    actions = each.value.actions
    principals {
      type = "AWS"
      identifiers = [
        aws_iam_role.irsa_role[each.value.role].arn
      ]
    }
    resources = [
      # Grant access only to the bucket and its contents
      aws_s3_bucket.user_buckets[each.value.bucket].arn,
      "${aws_s3_bucket.user_buckets[each.value.bucket].arn}/*",
    ]
  }
}

resource "aws_s3_bucket_policy" "user_bucket_access" {
  for_each = { for index, hrb in local.hub_role_bucket : hrb.id => hrb }
  bucket   = aws_s3_bucket.user_buckets[each.value.bucket].id
  policy   = data.aws_iam_policy_document.bucket_admin_access[each.key].json
}
