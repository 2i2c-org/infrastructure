region                 = "us-east-2"
cluster_name           = "smithsonian"
cluster_nodes_location = "us-east-2b"

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
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : ""
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch"],
    extra_iam_policy : ""
  },
}
