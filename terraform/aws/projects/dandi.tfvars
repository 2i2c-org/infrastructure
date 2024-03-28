region = "us-east-2"

cluster_name = "dandi"

cluster_nodes_location = "us-east-2a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch-dandi" : {
    "delete_after" : 7
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : ""
  },
  "dandi" : {
    bucket_admin_access : ["scratch-dandi"],
    extra_iam_policy : ""
  },
}