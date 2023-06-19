prefix     = "callysto"
project_id = "callysto-202316"

zone   = "northamerica-northeast1-b"
region = "northamerica-northeast1"

k8s_versions = {
  min_master_version : "1.25.6-gke.1000",
  core_nodes_version : "1.25.6-gke.1000",
  notebook_nodes_version : "1.25.6-gke.1000",
}

core_node_machine_type = "n2-highmem-2"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n2-highmem-4"
  },
}

user_buckets = {}
