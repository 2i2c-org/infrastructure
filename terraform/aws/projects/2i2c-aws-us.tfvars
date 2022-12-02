region = "us-west-2"

cluster_name = "2i2c-aws-us"

cluster_nodes_location = "us-west-2a"

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch-dask-staging": {
        "delete_after": 7
    },
    "scratch-research-delight": {
        "delete_after": 7
    },
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
    extra_iam_policy: ""
  },
  "dask-staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-dask-staging"],
    extra_iam_policy: ""
  },
  "research-delight" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-research-delight"],
    extra_iam_policy: ""
  },
}
