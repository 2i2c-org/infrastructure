region                 = "us-west-2"
cluster_name           = "openscapeshub"
cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

enable_aws_ce_grafana_backend_iam = true
disable_cluster_wide_filestore    = true

# The initial EFS is now used by the prod hub only
# So we tag it appropriately for costs purposes
original_single_efs_tags = { "2i2c:hub-name" : "prod" }

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "workshop" = {
    size        = 128
    type        = "gp3"
    name_suffix = "workshop"
    tags        = { "2i2c:hub-name" : "workshop" }
  },
  "prod" = {
    size        = 1536 # 1.5T
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
}
enable_nfs_backup = true

filestores = {}

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
    bucket_admin_access : [
      "scratch-staging",
      "persistent-staging",
    ],
  },
  "prod" : {
    bucket_admin_access : [
      "scratch",
      "persistent",
    ],
  },
  "workshop" : {
    bucket_admin_access : [
      "scratch-workshop",
      "persistent-workshop",
    ],
  },
}

active_cost_allocation_tags = [
  "2i2c:hub-name",
  "2i2c:node-purpose",
  "2i2c.org/cluster-name",
  "alpha.eksctl.io/cluster-name",
  "kubernetes.io/cluster/{var_cluster_name}",
  "kubernetes.io/created-for/pvc/name",
  "kubernetes.io/created-for/pvc/namespace",
]
