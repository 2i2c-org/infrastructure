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
}

ebs_volumes = {
  "staging" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
  "dask-staging" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "dask-staging"
    tags        = { "2i2c:hub-name" : "dask-staging" }
  }
  "showcase" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "showcase"
    tags        = { "2i2c:hub-name" : "showcase" }
  }
}

enable_nfs_backup = true