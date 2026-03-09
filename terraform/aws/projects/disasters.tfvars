region                 = "us-west-2"
cluster_name           = "disasters"
cluster_nodes_location = "us-west-2a"

enable_nfs_backup = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },

  "scratch-prod" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
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
              "arn:aws:s3:::veda-data-store",
              "arn:aws:s3:::veda-data-store/*",
              "arn:aws:s3:::cmip6-staging",
              "arn:aws:s3:::cmip6-staging/*",
              "arn:aws:s3:::lp-prod-protected",
              "arn:aws:s3:::lp-prod-protected/*",
              "arn:aws:s3:::gesdisc-cumulus-prod-protected",
              "arn:aws:s3:::gesdisc-cumulus-prod-protected/*",
              "arn:aws:s3:::nsidc-cumulus-prod-protected",
              "arn:aws:s3:::nsidc-cumulus-prod-protected/*",
              "arn:aws:s3:::ornl-cumulus-prod-protected",
              "arn:aws:s3:::ornl-cumulus-prod-protected/*",
              "arn:aws:s3:::pangeo-forge-veda-output",
              "arn:aws:s3:::pangeo-forge-veda-output/*",
              "arn:aws:s3:::podaac-ops-cumulus-public",
              "arn:aws:s3:::podaac-ops-cumulus-public/*",
              "arn:aws:s3:::podaac-ops-cumulus-protected",
              "arn:aws:s3:::podaac-ops-cumulus-protected/*",
              "arn:aws:s3:::usgs-landsat",
              "arn:aws:s3:::usgs-landsat/*",
              "arn:aws:s3:::nasa-disasters",
              "arn:aws:s3:::nasa-disasters/*",
              "arn:aws:s3:::sentinel-s2-l1c",
              "arn:aws:s3:::sentinel-s2-l1c/*",
              "arn:aws:s3:::csda-data-vendor-airbus-optical",
              "arn:aws:s3:::csda-data-vendor-airbus-optical/*",
              "arn:aws:s3:::csdap-ghgsat-delivery",
              "arn:aws:s3:::csdap-ghgsat-delivery/*",
              "arn:aws:s3:::csda-data-vendor-umbra",
              "arn:aws:s3:::csda-data-vendor-umbra/*",
              "arn:aws:s3:::csdap-capellaspace-delivery",
              "arn:aws:s3:::csdap-capellaspace-delivery/*",
              "arn:aws:s3:::csdap-airbus-delivery",
              "arn:aws:s3:::csdap-airbus-delivery/*",
              "arn:aws:s3:::csdap-blacksky-delivery",
              "arn:aws:s3:::csdap-blacksky-delivery/*",
              "arn:aws:s3:::csda-data-vendor-satellogic",
              "arn:aws:s3:::csda-data-vendor-satellogic/*",
              "arn:aws:s3:::csdap-iceye-delivery",
              "arn:aws:s3:::csdap-iceye-delivery/*",
              "arn:aws:s3:::naip-analytic",
              "arn:aws:s3:::naip-analytic/*"
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
    bucket_admin_access : ["scratch-prod"],
    extra_iam_policy : <<-EOT
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
              "arn:aws:s3:::veda-data-store",
              "arn:aws:s3:::veda-data-store/*",
              "arn:aws:s3:::cmip6-staging",
              "arn:aws:s3:::cmip6-staging/*",
              "arn:aws:s3:::lp-prod-protected",
              "arn:aws:s3:::lp-prod-protected/*",
              "arn:aws:s3:::gesdisc-cumulus-prod-protected",
              "arn:aws:s3:::gesdisc-cumulus-prod-protected/*",
              "arn:aws:s3:::nsidc-cumulus-prod-protected",
              "arn:aws:s3:::nsidc-cumulus-prod-protected/*",
              "arn:aws:s3:::ornl-cumulus-prod-protected",
              "arn:aws:s3:::ornl-cumulus-prod-protected/*",
              "arn:aws:s3:::pangeo-forge-veda-output",
              "arn:aws:s3:::pangeo-forge-veda-output/*",
              "arn:aws:s3:::podaac-ops-cumulus-public",
              "arn:aws:s3:::podaac-ops-cumulus-public/*",
              "arn:aws:s3:::podaac-ops-cumulus-protected",
              "arn:aws:s3:::podaac-ops-cumulus-protected/*",
              "arn:aws:s3:::usgs-landsat",
              "arn:aws:s3:::usgs-landsat/*",
              "arn:aws:s3:::nasa-disasters",
              "arn:aws:s3:::nasa-disasters/*",
              "arn:aws:s3:::sentinel-s2-l1c",
              "arn:aws:s3:::sentinel-s2-l1c/*",
              "arn:aws:s3:::csda-data-vendor-airbus-optical",
              "arn:aws:s3:::csda-data-vendor-airbus-optical/*",
              "arn:aws:s3:::csdap-ghgsat-delivery",
              "arn:aws:s3:::csdap-ghgsat-delivery/*",
              "arn:aws:s3:::csda-data-vendor-umbra",
              "arn:aws:s3:::csda-data-vendor-umbra/*",
              "arn:aws:s3:::csdap-capellaspace-delivery",
              "arn:aws:s3:::csdap-capellaspace-delivery/*",
              "arn:aws:s3:::csdap-airbus-delivery",
              "arn:aws:s3:::csdap-airbus-delivery/*",
              "arn:aws:s3:::csdap-blacksky-delivery",
              "arn:aws:s3:::csdap-blacksky-delivery/*",
              "arn:aws:s3:::csda-data-vendor-satellogic",
              "arn:aws:s3:::csda-data-vendor-satellogic/*",
              "arn:aws:s3:::csdap-iceye-delivery",
              "arn:aws:s3:::csdap-iceye-delivery/*",
              "arn:aws:s3:::naip-analytic",
              "arn:aws:s3:::naip-analytic/*"
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

ebs_volumes = {
  "staging" = {
    size        = 110
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 2500 # 2.5TB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  }
}

