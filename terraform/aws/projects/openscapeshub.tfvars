region                 = "us-west-2"
cluster_name           = "openscapeshub"
cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

enable_jupyterhub_cost_monitoring = true
enable_jupyterhub_cost_tags       = true
disable_cluster_wide_filestore    = true

# The initial EFS is now used by the prod hub only
# So we tag it appropriately for costs purposes
original_single_efs_tags = { "2i2c:hub-name" : "prod" }

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "workshop" = {
    size        = 100
    type        = "gp3"
    name_suffix = "workshop"
    tags        = { "2i2c:hub-name" : "workshop" }
  },
  "prod" = {
    size        = 1536 # 1.5T
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
}
enable_nfs_backup = true

filestores = {}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "prod-homedirs-archive" : {
    "archival_storageclass_after" : 3,
    "delete_after" : 185,
  },
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-workshop" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : [
      "scratch-staging",
      "persistent-staging",
    ],
    # Provides readonly requestor-pays access to firms-landsat-output bucket,
    # veda bucket (https://2i2c.freshdesk.com/a/tickets/6142).
    extra_iam_policy : <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:Get*",
                    "s3:List*",
                    "s3:Describe*"
                ],
                "Resource": [
                  "arn:aws:s3:::firms-landsat-output",
                  "arn:aws:s3:::firms-landsat-output/*"
                ]
            }
        ]
      }
    EOT
  },
  "prod" : {
    bucket_admin_access : [
      "scratch",
      "persistent",
    ],
    # Provides readonly requestor-pays access to firms-landsat-output bucket,
    # veda bucket (https://2i2c.freshdesk.com/a/tickets/6142).
    extra_iam_policy : <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:Get*",
                    "s3:List*",
                    "s3:Describe*"
                ],
                "Resource": [
                  "arn:aws:s3:::firms-landsat-output",
                  "arn:aws:s3:::firms-landsat-output/*"
                ]
            }
        ]
      }
    EOT
  },
  "workshop" : {
    bucket_admin_access : [
      "scratch-workshop",
      "persistent-workshop",
    ],
  },
}
