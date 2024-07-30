region = "us-west-2"

cluster_name = "openscapeshub"

cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

# Remove this variable to tag all our resources with {"ManagedBy": "2i2c"}
tags = {}

filestores = {
  "staging" = {
    name_suffix = "staging"
    tags = {
      "2i2c:hub-name": "staging"
    }
  }
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "prod-homedirs-archive" : {
    "archival_storageclass_after" : 3,
    "delete_after" : 185,
  },
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-workshop" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
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
