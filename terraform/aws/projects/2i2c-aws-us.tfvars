region                 = "us-west-2"
cluster_name           = "2i2c-aws-us"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = false

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch-dask-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "dask-staging" },
  },
  "scratch-showcase" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "showcase" },
  },
  "persistent-showcase" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "showcase" },
  },
  "scratch-ncar-cisl" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "ncar-cisl" },
  },
  "scratch-itcoocean" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "itcoocean" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "dask-staging" : {
    bucket_admin_access : ["scratch-dask-staging"],
  },
  "showcase" : {
    bucket_admin_access : [
      "scratch-showcase",
      "persistent-showcase",
    ],
  },
  "ncar-cisl" : {
    bucket_admin_access : ["scratch-ncar-cisl"],
  },
  "itcoocean" : {
    bucket_admin_access : ["scratch-itcoocean"],
  },
}
