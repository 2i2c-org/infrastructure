region                 = "us-east-2"
cluster_name           = "earthscope"
cluster_nodes_location = "us-east-2a"

tags = {
  "2i2c.org/cluster-name" : "{var_cluster_name}",
  "ManagedBy" : "2i2c",
  # Requested by the community in https://2i2c.freshdesk.com/a/tickets/1460
  "earthscope:application:name" : "geolab",
  "earthscope:application:owner" : "research-onramp-to-the-cloud",
}

default_budget_alert = {
  "enabled" : false,
}

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
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : ["scratch"],
    },
  },
}
