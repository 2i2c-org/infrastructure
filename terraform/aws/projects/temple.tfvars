region                 = "us-west-2"
cluster_name           = "temple"
cluster_nodes_location = "us-west-2a"

enable_nfs_backup = true

filestores = {}

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "advanced" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "advanced"
    tags        = { "2i2c:hub-name" : "advanced" }
  },
  "prod" = {
    size        = 1200 # in GB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
  "research" = {
    size        = 100 # in GB
    type        = "gp3"
    name_suffix = "research"
    tags        = { "2i2c:hub-name" : "research" }
  },
}

enable_jupyterhub_cost_monitoring = true

user_buckets = {
  "scratch-research" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "research" },
  },
}
