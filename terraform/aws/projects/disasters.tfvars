region                 = "us-west-2"
cluster_name           = "disasters"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true

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

ebs_volumes = {
  "staging" = {
    size        = 110
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 2500 # 2.5TB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  }
}

enable_nfs_backup = true