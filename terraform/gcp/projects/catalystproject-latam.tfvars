prefix                = "latam"
project_id            = "catalystproject-392106"
region                = "southamerica-east1"
zone                  = "southamerica-east1-c"
regional_cluster      = true
enable_network_policy = true

k8s_versions = {
  min_master_version : "1.27.2-gke.1200",
  core_nodes_version : "1.27.2-gke.1200",
  notebook_nodes_version : "1.27.2-gke.1200",
}

enable_filestore      = true
filestore_capacity_gb = 1024

core_node_machine_type = "n2-highmem-2"

notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  },
}

user_buckets = {}
