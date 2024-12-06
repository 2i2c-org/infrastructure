region                 = "af-south-1"
cluster_name           = "catalystproject-africa"
cluster_nodes_location = "af-south-1a"

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
  "persistent-bhki" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "bhki" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "prod" : {
    bucket_admin_access : ["scratch"],
  },
  "bhki" : {
    bucket_admin_access : ["persistent-bhki"],
  },
}
