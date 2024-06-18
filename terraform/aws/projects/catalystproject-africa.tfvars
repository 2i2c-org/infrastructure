region = "af-south-1"

cluster_name = "catalystproject-africa"

cluster_nodes_location = "af-south-1a"

# Remove this variable to tag all our resources with {"ManagedBy": "2i2c"}
tags = {}

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
