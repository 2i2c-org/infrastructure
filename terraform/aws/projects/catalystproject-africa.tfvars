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

ebs_volumes = {
  "uvri" = {
    size        = 1
    type        = "gp3"
    name_suffix = "uvri"
    tags        = { "2i2c:hub-name" : "uvri" }
  },
  "bhki" = {
    size        = 512
    type        = "gp3"
    name_suffix = "bhki"
    tags        = { "2i2c:hub-name" : "bhki" }
  },
  "must" = {
    size        = 64
    type        = "gp3"
    name_suffix = "must"
    tags        = { "2i2c:hub-name" : "must" }
  },
  "nm-aist" = {
    size        = 1
    type        = "gp3"
    name_suffix = "nm-aist"
    tags        = { "2i2c:hub-name" : "nm-aist" }
  },
  "molerhealth" = {
    size        = 256
    type        = "gp3"
    name_suffix = "molerhealth"
    tags        = { "2i2c:hub-name" : "molerhealth" }
  },
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "aibst" = {
    size        = 64
    type        = "gp3"
    name_suffix = "aibst"
    tags        = { "2i2c:hub-name" : "aibst" }
  },
  "kush" = {
    size        = 1
    type        = "gp3"
    name_suffix = "kush"
    tags        = { "2i2c:hub-name" : "kush" }
  },
  "wits" = {
    size        = 1
    type        = "gp3"
    name_suffix = "wits"
    tags        = { "2i2c:hub-name" : "wits" }
  },
  "bon" = {
    size        = 1
    type        = "gp3"
    name_suffix = "bon"
    tags        = { "2i2c:hub-name" : "bon" }
  }
}

enable_nfs_backup = true