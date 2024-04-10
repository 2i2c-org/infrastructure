region = "ca-central-1"

cluster_name = "ubc-eoas"

cluster_nodes_location = "ca-central-1a"

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
      extra_iam_policy : "",
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch"],
      extra_iam_policy : "",
    },
  },
}
