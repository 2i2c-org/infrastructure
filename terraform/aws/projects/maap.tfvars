region                 = "us-west-2"
cluster_name           = "maap"
cluster_nodes_location = "us-west-2a"

default_budget_alert = {
  "enabled" : false,
}

enable_aws_ce_grafana_backend_iam = true

filestores = {
  "staging" = {
    name_suffix = "staging",
    tags        = { "2i2c:hub-name" : "staging" },
  },
  "prod" = {
    name_suffix = "prod",
    tags        = { "2i2c:hub-name" : "prod" },
  },
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },

  "scratch-prod" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch-prod"],
  },
}
