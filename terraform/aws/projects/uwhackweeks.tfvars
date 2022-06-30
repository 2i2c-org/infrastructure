region = "us-west-2"

cluster_name = "uwhackweeks"

cluster_nodes_location = "us-west-2b"

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch": {
        "delete_after": 7
    },
    "snowex-scratch": {
        "delete_after": 7
    }
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
    extra_iam_policy: ""
  },
  "prod" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch"],
    extra_iam_policy: ""
  },
  "snowex" : {
    requestor_pays: true,
    bucket_admin_access: ["snowex-scratch"],
    # Grant S3 access to S3 buckets in other accounts
    # See https://github.com/2i2c-org/infrastructure/issues/1455
    extra_iam_policy: <<-EOT
      {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                  "arn:aws:s3:::dinosar",
                  "arn:aws:s3:::eis-dh-hydro"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                  "arn:aws:s3:::dinosar/*",
                  "arn:aws:s3:::eis-dh-hydro/*"
                ]
            }
        ]
      }
  EOT
  }
}
