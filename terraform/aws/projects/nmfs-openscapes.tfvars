region                 = "us-west-2"
cluster_name           = "nmfs-openscapes"
cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

disable_cluster_wide_filestore = true
filestores = {
  "staging" = {
    name_suffix = "staging",
    tags        = { "2i2c:hub-name" : "staging" },
  },
  "prod" = {
    name_suffix = "prod",
    tags        = { "2i2c:hub-name" : "prod" },
  },
}

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
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "tags" : { "2i2c:hub-name" : "prod" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging", "persistent-staging"],
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch", "persistent"],
    },
  },
}
