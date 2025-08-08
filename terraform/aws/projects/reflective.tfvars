region                 = "us-west-2"
cluster_name           = "reflective"
cluster_nodes_location = "us-west-2a"

enable_jupyterhub_cost_monitoring = true

enable_efs_backup = false
enable_nfs_backup = true
ebs_volumes = {
  "staging" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
  "workshop" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "workshop"
    tags        = { "2i2c:hub-name" : "workshop" }
  }
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
  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "persistent-staging" : {
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent-prod" : {
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-workshop" : {
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch-prod", "persistent-prod"],
  },
  "workshop" : {
    bucket_admin_access : ["scratch-workshop", "persistent-workshop"],
  },
}
