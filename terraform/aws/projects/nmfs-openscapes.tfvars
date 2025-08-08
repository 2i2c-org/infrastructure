region                 = "us-west-2"
cluster_name           = "nmfs-openscapes"
cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

enable_jupyterhub_cost_monitoring = true

disable_cluster_wide_filestore = true
ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 512
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
  "workshop" = {
    size        = 128
    type        = "gp3"
    name_suffix = "workshop"
    tags        = { "2i2c:hub-name" : "workshop" }
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
  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "persistent-staging" : {
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-workshop" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "scratch-noaa-only" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "noaa-only" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch", "persistent"],
  },
  "workshop" : {
    bucket_admin_access : [
      "scratch-workshop",
      "persistent-workshop",
    ],
  },
  "noaa-only" : {
    bucket_admin_access : ["scratch-noaa-only"],
  },
}

active_cost_allocation_tags = [
  "2i2c:hub-name",
  "2i2c.org/cluster-name",
  "alpha.eksctl.io/cluster-name",
  "kubernetes.io/cluster/{var_cluster_name}",
  "kubernetes.io/created-for/pvc/namespace",
]
