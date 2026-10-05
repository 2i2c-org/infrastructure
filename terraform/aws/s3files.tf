resource "aws_iam_role" "s3files" {
  for_each = local.s3files_hubs
  name     = "${var.cluster_name}-s3files-${each.key}"

  assume_role_policy = data.aws_iam_policy_document.s3files_assume_role.json
}

# from https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files-prereq-policies.html#s3-files-prereq-iam-creation-role
data "aws_iam_policy_document" "s3files_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type = "Service"

      identifiers = [
        "elasticfilesystem.amazonaws.com"
      ]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:s3files:${var.region}:${
        data.aws_caller_identity.current.account_id}:file-system/*"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        data.aws_caller_identity.current.account_id
      ]
    }
  }
}

# From https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-files-prereq-policies.html#s3-files-prereq-iam
resource "aws_iam_policy" "s3files_access" {
  for_each = local.s3files_hubs
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "S3BucketPermissions",
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket",
          "s3:ListBucketVersions"
        ],
        "Resource" : "arn:aws:s3:::${each.value.config.bucket}",
        "Condition" : {
          "StringEquals" : {
            "aws:ResourceAccount" : data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        "Sid" : "S3ObjectPermissions",
        "Effect" : "Allow",
        "Action" : [
          "s3:AbortMultipartUpload",
          "s3:DeleteObject*",
          "s3:GetObject*",
          "s3:List*",
          "s3:PutObject*"
        ],
        "Resource": "arn:aws:s3:::${each.value.config.bucket}/*",
        "Condition" : {
          "StringEquals" : {
            "aws:ResourceAccount" : data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        "Sid" : "UseKmsKeyWithS3Files",
        "Effect" : "Allow",
        "Action" : [
          "kms:GenerateDataKey",
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncryptFrom",
          "kms:ReEncryptTo"
        ],
        "Condition" : {
          "StringLike" : {
            "kms:ViaService" : "s3.${var.region}.amazonaws.com",
            "kms:EncryptionContext:aws:s3:arn" : [
              "arn:aws:s3:::${each.value.config.bucket}/*",
              "arn:aws:s3:::${each.value.config.bucket}"
            ]
          }
        },
        "Resource" : "arn:aws:kms:${var.region}:${ data.aws_caller_identity.current.account_id}:*"
      },
      {
        "Sid" : "EventBridgeManage",
        "Effect" : "Allow",
        "Action" : [
          "events:DeleteRule",
          "events:DisableRule",
          "events:EnableRule",
          "events:PutRule",
          "events:PutTargets",
          "events:RemoveTargets"
        ],
        "Condition" : {
          "StringEquals" : {
            "events:ManagedBy" : "elasticfilesystem.amazonaws.com"
          }
        },
        "Resource" : [
          "arn:aws:events:*:*:rule/DO-NOT-DELETE-S3-Files*"
        ]
      },
      {
        "Sid" : "EventBridgeRead",
        "Effect" : "Allow",
        "Action" : [
          "events:DescribeRule",
          "events:ListRuleNamesByTarget",
          "events:ListRules",
          "events:ListTargetsByRule"
        ],
        "Resource" : [
          "arn:aws:events:*:*:rule/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3files_attachment" {
  for_each = local.s3files_hubs
  role = aws_iam_role.s3files[each.key].name
  policy_arn = aws_iam_policy.s3files_access[each.key].arn
}

# We have to create one s3files per bucket per hub,
# since we want to use the same IAM role for bucket access
# when users use it via programmatic APIs talking to S3 *or*
# if they use s3files to access it.
resource "aws_s3files_file_system" "s3files" {
  for_each = local.s3files_hubs
  tags     = merge(each.value.config.tags, {
    "2i2c:hub-name": each.value.hub_name,
    "JHCM:HubName": each.value.hub_name
  })

  bucket                = "arn:aws:s3:::${each.value.config.bucket}"
  role_arn              = aws_iam_role.s3files[each.key].arn
  accept_bucket_warning = true

  lifecycle {
    # Additional safeguard against deleting the EFS
    # as this causes irreversible data loss!
    # prevent_destroy = true
  }
}

resource "aws_s3files_synchronization_configuration" "s3files" {
  for_each = local.s3files_hubs

  file_system_id = aws_s3files_file_system.s3files[each.key].id

  import_data_rule {
    prefix = ""
    # Don't import data into EFS at all, stream directly
    # This helps as we're using this for data access
    # Tune later if we want to have higher performance at higher cost
    size_less_than = 0
    trigger        = "ON_FILE_ACCESS"
  }

  expiration_data_rule {
    days_after_last_access = 3
  }
}

locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  s3files_hubs = { for s3fh in distinct(flatten([
    for s3filesname, config in var.s3files : [
      for hub_name in config.hubs : {
        hub_name      = hub_name
        s3filesname   = s3filesname
        config = config
      }
    ]
  ])) : "${s3fh.s3filesname}-${s3fh.hub_name}" => s3fh }

  s3files_hubs_mountpoints = { for s3hm in distinct(flatten([
    for key, value in local.s3files_hubs : [
      for subnet_id in toset(data.aws_subnets.cluster_node_subnets.ids) : {
        subnet_id: subnet_id,
        s3files_hubs_key: key
      }
    ]
  ])) : "${s3hm.subnet_id}-${s3hm.s3files_hubs_key}" => s3hm }
  # setproduct works with sets and lists, but aws_efs_file_system.hub_homedirs
  # is a map so convert it first
  file_systems = [
    for _, fs in aws_s3files_file_system.s3files : {
      id = fs.id
      # name = fs.tags["Name"]
    }
  ]

  # subnet_ids = toset(data.aws_subnets.cluster_node_subnets.ids)

  # # This variable is used to find the number of and construct all the
  # # indexes of the items in aws_efs_mount_target.hub_homedirs[*]
  # s3files_mount_targets = [
  #   # setproduct function will computing the Cartesian product
  #   # between the ids of each subnet and the given name of each EFS instance
  #   for pair in setproduct(toset(data.aws_subnets.cluster_node_subnets.ids), local.file_systems) : {
  #     subnet_id      = pair[0]
  #     file_system_id = pair[1].id
  #     # # Note that the id alone is not enough because terraform needs to know its
  #     # # value at plan time and this is not possible
  #     # name = pair[1].name
  #   }
  # ]
}

resource "aws_s3files_mount_target" "s3files" {
  for_each = local.s3files_hubs_mountpoints

  file_system_id  = aws_s3files_file_system.s3files[each.value.s3files_hubs_key].id
  subnet_id       = each.value.subnet_id
  security_groups = [data.aws_security_group.cluster_nodes_shared_security_group.id]
}

output "s3fs_fs_mape" {
  value = { for key, config in local.s3files_hubs : key => aws_s3files_file_system.s3files[key].id}
}
