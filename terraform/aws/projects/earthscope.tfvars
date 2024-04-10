region = "us-east-2"

cluster_name = "earthscope"

cluster_nodes_location = "us-east-2a"

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
