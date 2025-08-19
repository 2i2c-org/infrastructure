region                 = "us-west-2"
cluster_name           = "victor"
cluster_nodes_location = "us-west-2a"

disable_cluster_wide_filestore = true

default_budget_alert = {
  "enabled" = false
}
user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" }
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" }
  },
}
hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch"],
  },
}
ebs_volumes = {
  "staging" = {
    size        = 10 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
  "prod" = {
    size        = 1200 # in GB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  }
}

enable_nfs_backup = true
