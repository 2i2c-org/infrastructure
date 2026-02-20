region                 = "us-west-2"
cluster_name           = "maap"
cluster_nodes_location = "us-west-2a"

default_budget_alert = {
  "enabled" : false,
}

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
    max_session_duration : 12 * 60 * 60, # 12 hr max
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
              "arn:aws:s3:::veda-data-store",
              "arn:aws:s3:::veda-data-store/*",
              "arn:aws:s3:::veda-data-store-staging",
              "arn:aws:s3:::veda-data-store-staging/*",
              "arn:aws:s3:::veda-nex-gddp-cmip6-public",
              "arn:aws:s3:::veda-nex-gddp-cmip6-public/*",
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
              "arn:aws:s3:::ornl-cumulus-uat-public",
              "arn:aws:s3:::ornl-cumulus-uat-public/*",
              "arn:aws:s3:::ornl-cumulus-uat-protected",
              "arn:aws:s3:::ornl-cumulus-uat-protected/*",
              "arn:aws:s3:::pangeo-forge-veda-output",
              "arn:aws:s3:::pangeo-forge-veda-output/*",
              "arn:aws:s3:::podaac-ops-cumulus-public",
              "arn:aws:s3:::podaac-ops-cumulus-public/*",
              "arn:aws:s3:::podaac-ops-cumulus-protected",
              "arn:aws:s3:::podaac-ops-cumulus-protected/*",
              "arn:aws:s3:::maap-ops-workspace",
              "arn:aws:s3:::maap-ops-workspace/*",
              "arn:aws:s3:::nasa-maap-data-store",
              "arn:aws:s3:::nasa-maap-data-store/*",
              "arn:aws:s3:::sdap-dev-zarr",
              "arn:aws:s3:::sdap-dev-zarr/*",
              "arn:aws:s3:::usgs-landsat",
              "arn:aws:s3:::usgs-landsat/*",
              "arn:aws:s3:::sentinel-cogs",
              "arn:aws:s3:::sentinel-cogs/*",
              "arn:aws:s3:::sport-lis",
              "arn:aws:s3:::sport-lis/*",
              "arn:aws:s3:::nasa-disasters",
              "arn:aws:s3:::nasa-disasters/*",
              "arn:aws:s3:::nasa-eodc-scratch",
              "arn:aws:s3:::nasa-eodc-scratch/*"
            ]
          },
          {
            "Effect": "Allow",
            "Action": [
              "s3:PutObject",
              "s3:PutObjectAcl",
              "s3:PutObjectTagging",
              "s3:GetObjectTagging",
              "s3:ListBucket",
              "s3:DeleteObject",
              "s3:GetObject",
              "s3:RestoreObject",
              "s3:ListMultipartUploadParts",
              "s3:AbortMultipartUpload"
            ],
            "Resource": [
              "arn:aws:s3:::maap-ops-workspace",
              "arn:aws:s3:::maap-ops-workspace/*"
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
    max_session_duration : 12 * 60 * 60, # 12 hr max
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
              "arn:aws:s3:::veda-data-store",
              "arn:aws:s3:::veda-data-store/*",
              "arn:aws:s3:::veda-data-store-staging",
              "arn:aws:s3:::veda-data-store-staging/*",
              "arn:aws:s3:::veda-nex-gddp-cmip6-public",
              "arn:aws:s3:::veda-nex-gddp-cmip6-public/*",
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
              "arn:aws:s3:::ornl-cumulus-uat-public",
              "arn:aws:s3:::ornl-cumulus-uat-public/*",
              "arn:aws:s3:::ornl-cumulus-uat-protected",
              "arn:aws:s3:::ornl-cumulus-uat-protected/*",
              "arn:aws:s3:::pangeo-forge-veda-output",
              "arn:aws:s3:::pangeo-forge-veda-output/*",
              "arn:aws:s3:::podaac-ops-cumulus-public",
              "arn:aws:s3:::podaac-ops-cumulus-public/*",
              "arn:aws:s3:::podaac-ops-cumulus-protected",
              "arn:aws:s3:::podaac-ops-cumulus-protected/*",
              "arn:aws:s3:::maap-ops-workspace",
              "arn:aws:s3:::maap-ops-workspace/*",
              "arn:aws:s3:::nasa-maap-data-store",
              "arn:aws:s3:::nasa-maap-data-store/*",
              "arn:aws:s3:::sdap-dev-zarr",
              "arn:aws:s3:::sdap-dev-zarr/*",
              "arn:aws:s3:::usgs-landsat",
              "arn:aws:s3:::usgs-landsat/*",
              "arn:aws:s3:::sentinel-cogs",
              "arn:aws:s3:::sentinel-cogs/*",
              "arn:aws:s3:::sport-lis",
              "arn:aws:s3:::sport-lis/*",
              "arn:aws:s3:::nasa-disasters",
              "arn:aws:s3:::nasa-disasters/*"
            ]
          },
          {
            "Effect": "Allow",
            "Action": [
              "s3:PutObject",
              "s3:PutObjectAcl",
              "s3:PutObjectTagging",
              "s3:GetObjectTagging",
              "s3:ListBucket",
              "s3:DeleteObject",
              "s3:GetObject",
              "s3:RestoreObject",
              "s3:ListMultipartUploadParts",
              "s3:AbortMultipartUpload"
            ],
            "Resource": [
              "arn:aws:s3:::maap-ops-workspace",
              "arn:aws:s3:::maap-ops-workspace/*"
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
    size        = 100
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 2000 # 2TB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" },
    iops        = 5000
  }
}

enable_nfs_backup = true

enable_jupyterhub_cost_monitoring = true
