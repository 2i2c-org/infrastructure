region                 = "us-west-2"
cluster_name           = "victor"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = false

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" }
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" }
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
