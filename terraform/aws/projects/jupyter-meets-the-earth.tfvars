region = "us-west-2"

cluster_name = "jupyter-meets-the-earth"

cluster_nodes_location = "us-west-2a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging"],
      # FIXME: Previously, users were granted full S3 permissions.
      # Keep it the same for now
      extra_iam_policy : <<-EOT
{
  "Version": "2012-10-17",
  "Statement": [       
    {
        "Effect": "Allow",           
        "Action": ["s3:*"],           
        "Resource": ["arn:aws:s3:::*"]
    }
  ]
}
EOT
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch"],
      # FIXME: Previously, users were granted full S3 permissions.
      # Keep it the same for now
      extra_iam_policy : <<-EOT
{
  "Version": "2012-10-17",
  "Statement": [       
    {
        "Effect": "Allow",           
        "Action": ["s3:*"],           
        "Resource": ["arn:aws:s3:::*"]
    }
  ]
}
EOT
    },
  },
}
