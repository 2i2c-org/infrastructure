region = "us-west-2"

cluster_name = "nasa-cryo"

cluster_nodes_location = "us-west-2a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  # For https://2i2c.freshdesk.com/a/tickets/847
  "persistent-staging" : {
    "delete_after" : null,
  },
  "persistent" : {
    "delete_after" : null,
  },
}

hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging", "persistent-staging"],
      # Provides readonly requestor-pays access to usgs-landsat bucket
      # FIXME: We should find a way to allow access to *all* requester pays
      # buckets, without having to explicitly list them. However, we don't want
      # to give access to all *internal* s3 buckets willy-nilly - this can be
      # a massive security hole, especially if terraform state is also here.
      # As a temporary measure, we allow-list buckets here.
      extra_iam_policy : <<-EOT
        {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Effect": "Allow",
                  "Action": [
                      "s3:*"
                  ],
                  "Resource": [
                    "arn:aws:s3:::usgs-landsat"
                  ]
              },
              {
                  "Effect": "Allow",
                  "Action": [
                      "s3:*"
                  ],
                  "Resource": [
                    "arn:aws:s3:::usgs-landsat/*"
                  ]
              }
          ]
        }
    EOT
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch", "persistent"],
      # Provides readonly requestor-pays access to usgs-landsat bucket
      # FIXME: We should find a way to allow access to *all* requester pays
      # buckets, without having to explicitly list them. However, we don't want
      # to give access to all *internal* s3 buckets willy-nilly - this can be
      # a massive security hole, especially if terraform state is also here.
      # As a temporary measure, we allow-list buckets here.
      extra_iam_policy : <<-EOT
        {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Effect": "Allow",
                  "Action": [
                      "s3:*"
                  ],
                  "Resource": [
                    "arn:aws:s3:::usgs-landsat"
                  ]
              },
              {
                  "Effect": "Allow",
                  "Action": [
                      "s3:*"
                  ],
                  "Resource": [
                    "arn:aws:s3:::usgs-landsat/*"
                  ]
              }
          ]
        }
    EOT
    },
  },
}
