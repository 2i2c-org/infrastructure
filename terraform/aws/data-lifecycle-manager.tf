# ref: https://docs.aws.amazon.com/ebs/latest/userguide/snapshot-lifecycle.html
# Data Lifecycle Manager (DLM) is used to automate backup of EBS volumes.

resource "aws_iam_role" "dlm_lifecycle_role" {
  name = "dlm-lifecycle-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "dlm.amazonaws.com"
        }
      }
    ]
  })
}

# Attach required policy to the IAM role
resource "aws_iam_role_policy" "dlm_lifecycle" {
  name = "dlm-lifecycle-policy"
  role = aws_iam_role.dlm_lifecycle_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSnapshot",
          "ec2:CreateSnapshots",
          "ec2:DeleteSnapshot",
          "ec2:DescribeVolumes",
          "ec2:DescribeInstances",
          "ec2:DescribeSnapshots"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*::snapshot/*"
      }
    ]
  })
}

# Create the DLM lifecycle policy for NFS home directories backup
resource "aws_dlm_lifecycle_policy" "nfs_backup" {
  description        = "DLM lifecycle policy for NFS home directories backup"
  execution_role_arn = aws_iam_role.dlm_lifecycle_role.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    schedule {
      name = "Daily backup"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["23:45"]
      }

      retain_rule {
        count = 5 # Keep last 5 daily backups
      }

      tags_to_add = {
        SnapshotCreator = "DLM"
        Purpose         = "NFS-Backup"
      }

      copy_tags = true
    }

    target_tags = {
      NFSBackup = "true" # Tag to identify volumes to backup
    }
  }
}