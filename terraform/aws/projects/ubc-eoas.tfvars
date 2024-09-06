region                 = "ca-central-1"
cluster_name           = "ubc-eoas"
cluster_nodes_location = "ca-central-1a"

tags = {
  "2i2c.org/cluster-name" : "ubc-eoas",
  "ManagedBy" : "2i2c",
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging"],
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch"],
    },
  },
}
