region                 = "us-west-2"
cluster_name           = "2i2c-aws-us"
cluster_nodes_location = "us-west-2a"

enable_jupyterhub_cost_monitoring = true
disable_cluster_wide_filestore    = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch-showcase" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "showcase" },
  },
  "persistent-showcase" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "showcase" },
  },
  "scratch-orcid-demo" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "orcid-demo" },
  },
  "persistent-orcid-demo" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "orcid-demo" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "showcase" : {
    bucket_admin_access : [
      "scratch-showcase",
      "persistent-showcase",
    ],
  },
  "orcid-demo" : {
    bucket_admin_access : [
      "scratch-orcid-demo",
      "persistent-orcid-demo"
    ],
    extra_iam_policy : <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": "s3:ListAllMyBuckets",
            "Resource": "*"
          }
        ]
      }
    EOT
  }
}

ebs_volumes = {
  "staging" = {
    size        = 10 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
  "showcase" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "showcase"
    tags        = { "2i2c:hub-name" : "showcase" }
  }
  "orcid-demo" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "orcid-demo"
    tags        = { "2i2c:hub-name" : "orcid-demo" }
  }

}

enable_nfs_backup = true