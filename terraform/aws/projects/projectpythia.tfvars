region                 = "us-west-2"
cluster_name           = "projectpythia"
cluster_nodes_location = "us-west-2a"

default_budget_alert = {
  "enabled" : false,
}

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = false

# FIXME: placeholder bucket to get the 2i2c:hub-name tag in place
# so the community cand enable it for cost allocation purposes
# To be removed once it has been activated.
user_buckets = {
  "placeholder-bucket-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["placeholder-bucket-staging"],
  },
}