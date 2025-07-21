prefix     = "climatematch"
project_id = "climatematch"

zone   = "us-central1-b"
region = "us-central1"

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.32.2-gke.1182003",
  core_nodes_version : "1.32.2-gke.1182003",
  notebook_nodes_version : "1.32.2-gke.1182003",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  }
}

filestores = {}

persistent_disks = {
  "staging" = {
    size        = 1 # in GB
    name_suffix = "staging"
  },

  "prod" = {
    size        = 88 # in GB
    name_suffix = "prod"
  }
}