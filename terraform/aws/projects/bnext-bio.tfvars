region                 = "us-west-2"
cluster_name           = "bnext-bio"
cluster_nodes_location = "us-west-2a"

ebs_volumes = {
  "staging" = {
    name_suffix = "staging",
    type        = "gp3",
    size        = 10,
    tags        = { "2i2c:hub-name" : "staging" },
  },
  "prod" = {
    name_suffix = "prod",
    type        = "gp3",
    size        = 100,
    tags        = { "2i2c:hub-name" : "prod" },
  },

}
enable_nfs_backup = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" },

  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" },
  }
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch", "persistent"],
  }
}

enable_jupyterhub_cost_monitoring = true
