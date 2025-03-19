region                 = "us-west-2"
cluster_name           = "opensci"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch-sciencecore" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "sciencecore" },
  },
  "persistent-sciencecore" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "sciencecore" },
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
  },
  "sciencecore" : {
    bucket_admin_access : ["scratch-sciencecore"],
    bucket_readonly_access : ["persistent-sciencecore"],
  },
}

enable_nfs_backup = true

ebs_volumes = {
  "staging" = {
    size        = 10 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
  "sciencecore" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "sciencecore"
    tags        = { "2i2c:hub-name" : "sciencecore" }
  }
  "climaterisk" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "climaterisk"
    tags        = { "2i2c:hub-name" : "climaterisk" }
  }
}
