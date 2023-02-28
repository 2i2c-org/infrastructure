region = "us-west-2"

cluster_name = "nasa-veda"

cluster_nodes_location = "us-west-2a"

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch": {
        "delete_after": 7
    },
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
    extra_iam_policy: <<-EOT
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucketMultipartUploads",
                    "s3:AbortMultipartUpload",
                    "s3:ListBucketVersions",
                    "s3:CreateBucket",
                    "s3:ListBucket",
                    "s3:DeleteObject",
                    "s3:GetBucketLocation",
                    "s3:ListMultipartUploadParts"
                ],
                "Resource": [
                    "arn:aws:s3:::veda-data-store-staging",
                    "arn:aws:s3:::veda-data-store-staging/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*"
            }
        ]
    }
  EOT
  },
  "prod" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch"],
    extra_iam_policy: <<-EOT
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucketMultipartUploads",
                    "s3:AbortMultipartUpload",
                    "s3:ListBucketVersions",
                    "s3:CreateBucket",
                    "s3:ListBucket",
                    "s3:DeleteObject",
                    "s3:GetBucketLocation",
                    "s3:ListMultipartUploadParts"
                ],
                "Resource": [
                    "arn:aws:s3:::veda-data-store-staging",
                    "arn:aws:s3:::veda-data-store-staging/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*"
            }
        ]
    }
  EOT
  },
}
