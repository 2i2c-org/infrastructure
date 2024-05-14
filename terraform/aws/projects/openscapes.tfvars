region = "us-west-2"

cluster_name = "openscapeshub"

cluster_nodes_location = "us-west-2b"

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  "scratch-workshop" : {
    "delete_after" : 7
  },
  "prod-homedirs-archive" : {
    "archival_storageclass_after" : 3
  },
  "persistent-staging" : {
    "delete_after" : null
  },
  "persistent" : {
    "delete_after" : null
  },
  "persistent-workshop" : {
    "delete_after" : null
  }
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch-staging",
        "persistent-staging",
      ],
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch",
        "persistent",
      ],
    }
  },
  "workshop" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch-workshop",
        "persistent-workshop",
      ],
    }
  },
}
