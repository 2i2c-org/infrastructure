region                 = "us-west-2"
cluster_name           = "opensci"
cluster_nodes_location = "us-west-2a"

tags = {
  "2i2c.org/cluster-name" : "opensci",
  "ManagedBy" : "2i2c",
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch-sciencecore" : {
    "delete_after" : 7
  },
  "persistent-sciencecore" : {
    "delete_after" : null
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging"],
    },
  },
  "sciencecore" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-sciencecore"],
      bucket_readonly_access : ["persistent-sciencecore"],
    },
    "admin-sa" : {
      bucket_admin_access : ["scratch-sciencecore", "persistent-sciencecore"],
    },
  },
}
