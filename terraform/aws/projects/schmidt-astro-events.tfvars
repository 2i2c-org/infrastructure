region                 = "us-east-1"
cluster_name           = "schmidt-astro-events"
cluster_nodes_location = "us-east-1a"

ebs_volumes = {
  "staging" = {
    name_suffix = "staging",
    type        = "gp3",
    size        = 10,
    tags = {
      "2i2c:hub-name" : "staging",
      "JHCM:HubName" : "staging"
    },
  },
  "workshop" = {
    name_suffix = "workshop",
    type        = "gp3",
    size        = 100,
    tags = {
      "2i2c:hub-name" : "workshop"
      "JHCM:HubName" : "staging"
    },
  },

}
enable_nfs_backup = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : {
      "2i2c:hub-name" : "staging"
      "JHCM:HubName" : "staging"
    },
  },

  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : {
      "2i2c:hub-name" : "workshop",
      "JHCM:HubName" : "workshop"
    },
  },
}


hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": [
              "s3:GetObject",
              "s3:GetObjectTagging",
              "s3:ListBucketVersions",
              "s3:ListBucket",
              "s3:GetBucketLocation"
            ],
            "Resource": [
              "arn:aws:s3:::schmidt-observatory-system",
              "arn:aws:s3:::schmidt-observatory-system/*",
              "arn:aws:s3:::schmidt-yuvi-test-bucket",
              "arn:aws:s3:::schmidt-yuvi-test-bucket/*"
            ]
          }
        ]
      }
    EOT
  },
  "workshop" : {
    bucket_admin_access : ["scratch-workshop"],
    extra_iam_policy : <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
          {
            "Effect": "Allow",
            "Action": [
              "s3:GetObject",
              "s3:GetObjectTagging",
              "s3:ListBucketVersions",
              "s3:ListBucket",
              "s3:GetBucketLocation"
            ],
            "Resource": [
              "arn:aws:s3:::schmidt-observatory-system",
              "arn:aws:s3:::schmidt-observatory-system/*",
              "arn:aws:s3:::schmidt-yuvi-test-bucket",
              "arn:aws:s3:::schmidt-yuvi-test-bucket/*"
            ]
          }
        ]
      }
    EOT
  },
}

enable_jupyterhub_cost_monitoring = true

s3files = {
  "schmidt-observatory-system" : {
    tags = {
      "2i2c:hub-name" : "workshop",
      "JHCM:HubName" : "workshop"
    },
    bucket = "schmidt-observatory-system"
    hubs   = ["workshop", "staging"]
  }
}