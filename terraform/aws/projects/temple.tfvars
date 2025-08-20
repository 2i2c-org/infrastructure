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
  "prod" = {
    size        = 100 # in GB 
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
}

