region                 = "us-west-2"
cluster_name           = "2i2c-aws-us"
cluster_nodes_location = "us-west-2a"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch-dask-staging" : {
    "delete_after" : 7
  },
  "scratch-showcase" : {
    "delete_after" : 7
  },
  "persistent-showcase" : {
    "delete_after" : null
  },
  "scratch-ncar-cisl" : {
    "delete_after" : 7
  },
  "scratch-itcoocean" : {
    "delete_after" : 7
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging"],
    },
  },
  "dask-staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-dask-staging"],
    },
  },
  "showcase" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch-showcase",
        "persistent-showcase",
      ],
    },
  },
  "ncar-cisl" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-ncar-cisl"],
    },
  },
  "itcoocean" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-itcoocean"],
    },
  },
}
