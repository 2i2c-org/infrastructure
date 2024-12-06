region                 = "us-east-2"
cluster_name           = "earthscope"
cluster_nodes_location = "us-east-2a"

default_tags = {
  "2i2c.org/cluster-name" : "earthscope",
  "ManagedBy" : "2i2c",
  # Requested by the community in https://2i2c.freshdesk.com/a/tickets/1460
  "earthscope:application:name" : "geolab",
  "earthscope:application:owner" : "research-onramp-to-the-cloud",
}

default_budget_alert = {
  "enabled" : false,
}

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = false

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch"],
  },
}
