region = "af-south-1"

cluster_name = "catalystproject-africa"

cluster_nodes_location = "af-south-1a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  "persistent-bhki" : {
    "delete_after" : null
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
  "bhki" : {
    "user-sa" : {
      bucket_admin_access : ["persistent-bhki"],
    },
  },
}
