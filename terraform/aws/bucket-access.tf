/*
  Creates one aws_s3_bucket_policy per bucket - there can't be more than one as
  they otherwise replace each other when applied.

  The bucket policies grant bucket specific permissions to specific IAM Roles
  based on them having `bucket_admin_access` or `bucket_readonly_access`
  referencing the bucket via `var.hub_cloud_permissions`.
*/

locals {
  /*
    The bucket_role_actions local variable defined below is a list of objects
    generated from `var.hub_cloud_permissions` roles and their respective
    bucket_admin_access and bucket_readonly_access lists.

    If for example `var.hub_cloud_permissions` is:

    hub_cloud_permissions:
      staging:
        user-sa:
          bucket_admin_access: [scratch-staging]
      sciencecore:
        user-sa:
          bucket_admin_access: [scratch-sciencecore]
          bucket_readonly_access: [persistent-sciencecore]
        admin-sa:
          bucket_admin_access: [scratch-sciencecore, persistent-sciencecore]

    Then, the `local.bucket_role_actions` will look like below, with one list
    item for each element in all `bucket_admin/readonly_access` lists:

    bucket_role_actions:
      - bucket: scratch-staging
        role: staging
        actions: ["s3:*"]
      - bucket: scratch-sciencecore
        role: sciencecore
        actions: ["s3:*"]
      - bucket: scratch-sciencecore
        role: sciencecore-admin-sa
        actions: ["s3:*"]
      - bucket: persistent-sciencecore
        role: sciencecore
        actions: ["s3:ListBucket", "s3:GetObject", "s3:GetObjectVersion"]
      - bucket: persistent-sciencecore
        role: sciencecore
        actions: ["s3:*"]
  */
  bucket_role_actions = flatten([
    for hub, hub_value in var.hub_cloud_permissions : [
      for role, role_value in hub_value : flatten([
        [
          for bucket in role_value.bucket_admin_access : {
            bucket = bucket
            // role should match the id set in irsa.tf
            role    = role == "user-sa" ? hub : "${hub}-${role}"
            actions = ["s3:*"]
          }
        ],
        [
          for bucket in role_value.bucket_readonly_access : {
            bucket = bucket
            // role should match the id set in irsa.tf
            role = role == "user-sa" ? hub : "${hub}-${role}"
            actions = [
              "s3:ListBucket",
              "s3:GetObject",
              "s3:GetObjectVersion",
            ]
          }
        ],
      ])
    ]
  ])
}

locals {
  /*
    The `local.bucket_role_actions_lists` variable defined below is reprocessing
    `local.bucket_role_actions` to a dictionary with one key per bucket with
    associated permissions.

    bucket_role_actions_lists:
      scratch-staging:
        - bucket: scratch-staging
          role: staging
          actions: ["s3:*"]
      scratch-sciencecore:
        - bucket: scratch-sciencecore
          role: sciencecore
          actions: ["s3:*"]
        - bucket: scratch-sciencecore
          role: sciencecore-admin-sa
          actions: ["s3:*"]
      persistent-sciencecore:
        - bucket: persistent-sciencecore
          role: sciencecore
          actions: ["s3:ListBucket", "s3:GetObject", "s3:GetObjectVersion"]
        - bucket: persistent-sciencecore
          role: sciencecore
          actions: ["s3:*"]
  */
  bucket_role_actions_lists = {
    for bucket, _ in var.user_buckets :
    bucket => [for bra in local.bucket_role_actions : bra if bra.bucket == bucket]
    // Filter out user_buckets not mentioned in hub_cloud_permissions
    if length([for bra in local.bucket_role_actions : bra if bra.bucket == bucket]) != 0
  }
}



data "aws_iam_policy_document" "bucket_policy" {
  for_each = local.bucket_role_actions_lists

  // Only one policy document can be declared per bucket, so we provide multiple
  // "statement" in this policy.
  dynamic "statement" {
    for_each = { for index, bra in each.value : "${bra.bucket}.${bra.role}" => bra }

    content {
      effect  = "Allow"
      actions = statement.value.actions
      principals {
        type = "AWS"
        identifiers = [
          aws_iam_role.irsa_role[statement.value.role].arn
        ]
      }
      resources = [
        # Grant access only to the bucket and its contents
        aws_s3_bucket.user_buckets[statement.value.bucket].arn,
        "${aws_s3_bucket.user_buckets[statement.value.bucket].arn}/*",
      ]
    }
  }
}

// There can only be one of these per bucket, if more are defined they will end
// up replacing each other without terraform indicating there is trouble.
resource "aws_s3_bucket_policy" "user_bucket_access" {
  for_each = local.bucket_role_actions_lists
  bucket   = aws_s3_bucket.user_buckets[each.key].id
  policy   = data.aws_iam_policy_document.bucket_policy[each.key].json
}
