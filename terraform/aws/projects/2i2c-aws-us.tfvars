region = "us-west-2"

cluster_name = "2i2c-aws-us"

cluster_nodes_location = "us-west-2a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch-dask-staging" : {
    "delete_after" : 7
  },
  "scratch-researchdelight" : {
    "delete_after" : 7
  },
  "scratch-ncar-cisl" : {
    "delete_after" : 7
  },
  "scratch-go-bgc" : {
    "delete_after" : 7
  },
  "scratch-itcoocean" : {
    "delete_after" : 7
  },
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : ""
  },
  "dask-staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-dask-staging"],
    extra_iam_policy : ""
  },
  "researchdelight" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-researchdelight"],
    extra_iam_policy : ""
  },
  "ncar-cisl" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-ncar-cisl"],
    extra_iam_policy : ""
  },
  "go-bgc" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-go-bgc"],
    extra_iam_policy : ""
  },
  "itcoocean" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-itcoocean"],
    extra_iam_policy : ""
  },
}
