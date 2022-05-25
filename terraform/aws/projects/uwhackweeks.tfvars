region = "us-west-2"

cluster_name = "uwhackweeks"

cluster_nodes_location = "us-west-2b"

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch": {
        "delete_after": 7
    }
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
  },
  "prod" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch"],
  }
}