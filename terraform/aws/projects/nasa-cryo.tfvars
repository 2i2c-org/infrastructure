region                 = "us-west-2"
cluster_name           = "nasa-cryo"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 4250
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  }
}
enable_nfs_backup = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" }
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" }
  },
  # For https://2i2c.freshdesk.com/a/tickets/847
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" }
  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" }
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    # Provides readonly requestor-pays access to usgs-landsat bucket,
    # veda bucket (https://2i2c.freshdesk.com/a/tickets/1547) and sliderule
    # bucket (https://2i2c.freshdesk.com/a/tickets/1508).
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
                  "arn:aws:s3:::usgs-landsat",
                  "arn:aws:s3:::usgs-landsat/*",
                  "arn:aws:s3:::sliderule-public",
                  "arn:aws:s3:::sliderule-public/*",
                  "arn:aws:s3:::veda-data-store",
                  "arn:aws:s3:::veda-data-store/*",
                  "arn:aws:s3:::veda-data-store-staging",
                  "arn:aws:s3:::veda-data-store-staging/*",
                  "arn:aws:s3:::ghgc-data-store",
                  "arn:aws:s3:::ghgc-data-store/*"

                ]
            }
        ]
      }
    EOT
  },
  "prod" : {
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
                  "arn:aws:s3:::usgs-landsat",
                  "arn:aws:s3:::usgs-landsat/*",
                  "arn:aws:s3:::sliderule-public",
                  "arn:aws:s3:::sliderule-public/*",
                  "arn:aws:s3:::veda-data-store",
                  "arn:aws:s3:::veda-data-store/*",
                  "arn:aws:s3:::veda-data-store-staging",
                  "arn:aws:s3:::veda-data-store-staging/*",
                  "arn:aws:s3:::ghgc-data-store",
                  "arn:aws:s3:::ghgc-data-store/*"
                ]
            }
        ]
      }
    EOT
  },
}
