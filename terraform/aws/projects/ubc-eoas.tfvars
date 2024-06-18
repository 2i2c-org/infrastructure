region = "ca-central-1"

cluster_name = "ubc-eoas"

cluster_nodes_location = "ca-central-1a"

# Remove this variable to tag all our resources with {"ManagedBy": "2i2c"}
tags = {}

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
