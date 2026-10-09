locals {
  # Nested for loop, thanks to https://www.daveperrett.com/articles/2021/08/19/nested-for-each-with-terraform/
  s3files_hubs = { for s3fh in distinct(flatten([
    for s3filesname, config in var.s3files : [
      for hub_name in config.hubs : {
        hub_name    = hub_name
        s3filesname = s3filesname
        config      = config
      }
    ]
  ])) : "${s3fh.s3filesname}-${s3fh.hub_name}" => s3fh }

  s3files_hubs_mountpoints = { for s3hm in distinct(flatten([
    for key, value in local.s3files_hubs : [
      for subnet_id in toset(data.aws_subnets.cluster_node_subnets.ids) : {
        subnet_id : subnet_id,
        s3files_hubs_key : key
      }
    ]
  ])) : "${s3hm.subnet_id}-${s3hm.s3files_hubs_key}" => s3hm }
}

# IAM roles, one per s3file, that lets S3Files access the data
# as well as EventBridge & other permissions needed to set itself
# up. This is the role that needs appropriate access to the
# S3 buckets as well.
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
        "Resource" : "arn:aws:s3:::${each.value.config.bucket}/*",
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
        "Resource" : "arn:aws:kms:${var.region}:${data.aws_caller_identity.current.account_id}:*"
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

resource "aws_iam_role_policy_attachment" "s3files" {
  for_each   = local.s3files_hubs
  role       = aws_iam_role.s3files[each.key].name
  policy_arn = aws_iam_policy.s3files_access[each.key].arn
}

# We have to create one s3files per bucket per hub,
# so we can attribute cost of the access accurately at least
# to the hub, even if we can't to each user.
resource "aws_s3files_file_system" "s3files" {
  for_each = local.s3files_hubs
  tags = merge(each.value.config.tags, {
    "2i2c:hub-name" : each.value.hub_name,
    "JHCM:HubName" : each.value.hub_name
  })

  bucket                = "arn:aws:s3:::${each.value.config.bucket}"
  role_arn              = aws_iam_role.s3files[each.key].arn
  accept_bucket_warning = true

  lifecycle {
    # Additional safeguard against deleting the S3Files,
    # as recreating this means we have to change the
    # filesystem id in our helm config
    prevent_destroy = true
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
    # Only keep data for 3 days, to keep the amount of data
    # in EFS small.
    days_after_last_access = 3
  }
}

resource "aws_s3files_mount_target" "s3files" {
  for_each = local.s3files_hubs_mountpoints

  file_system_id  = aws_s3files_file_system.s3files[each.value.s3files_hubs_key].id
  subnet_id       = each.value.subnet_id
  security_groups = [data.aws_security_group.cluster_nodes_shared_security_group.id]
}


# Create a role for the EFS CSI driver, one per cluster
# This should be able to access all the S3 buckets we care
# about as well, since it may do direct reads too.
resource "aws_iam_role" "s3files_efs_csi_driver" {
  count = length(local.s3files_hubs) > 0 ? 1 : 0
  name  = "${var.cluster_name}-s3files-efs-csi-driver"

  assume_role_policy = data.aws_iam_policy_document.s3files_efs_csi_driver_assume.json
}

# Let this role be assumed by the efs node & controller
data "aws_iam_policy_document" "s3files_efs_csi_driver_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type = "Federated"

      identifiers = [
        "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values = [
        # Same role for both node & controller
        "system:serviceaccount:kube-system:efs-csi-node-sa",
        "system:serviceaccount:kube-system:efs-csi-controller-sa"
      ]
    }
  }
}

resource "aws_iam_role_policy_attachment" "s3files_efs_base" {
  # From https://docs.aws.amazon.com/eks/latest/userguide/s3files-csi.html
  # for the access that the EFS CSI driver needs
  for_each = length(local.s3files_hubs) > 0 ? toset([
    "arn:aws:iam::aws:policy/service-role/AmazonS3FilesCSIDriverPolicy",
    "arn:aws:iam::aws:policy/AmazonS3FilesClientFullAccess",

    # In the future, we can tune this to have ReadOnly access
    # just to specific buckets
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonElasticFileSystemsUtils"
  ]) : toset([])
  role       = aws_iam_role.s3files_efs_csi_driver[0].name
  policy_arn = each.value
}

output "s3files_fs_map" {
  value = {
    for hub_name, mounts in
    {
      for key, config in local.s3files_hubs
      :
      config.hub_name => {
        (config.config.bucket) = {
          "bucketName" : config.config.bucket, "volumeHandle" : aws_s3files_file_system.s3files[key].id
        }
      }...
    }
    :
    hub_name => yamlencode(merge(mounts...))
  }
}

#

output "s3files_efs_csi_driver_role" {
  value = one(aws_iam_role.s3files_efs_csi_driver[*].arn)
}
