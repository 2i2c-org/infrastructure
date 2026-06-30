region                 = "us-west-2"
cluster_name           = "neurohackademy"
cluster_nodes_location = "us-west-2a"

enable_jupyterhub_cost_monitoring = true

enable_nfs_backup = true

filestores = {}

ebs_volumes = {
  "staging" = {
    size        = 5 # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
  "prod" = {
    size        = 1000 # in GB
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
    iops        = 10000
  }
}

core_nodes = {
  machine_type : "r8i-flex.large"
}
notebook_nodes = {
  "r5-xlarge" : {
    min : 0,
    max : 100,
    machine_type : "r5.xlarge",
  },
  "r5-4xlarge" : {
    min : 0,
    max : 100,
    machine_type : "r5.4xlarge",
  },
  "r5-16xlarge" : {
    min : 0,
    max : 100,
    machine_type : "r5.16xlarge",
  }
}
