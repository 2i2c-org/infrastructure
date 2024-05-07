prefix     = "two-eye-two-see-uk"
project_id = "two-eye-two-see-uk"

zone   = "europe-west2-b"
region = "europe-west2"

k8s_versions = {
  min_master_version : "1.27.4-gke.900",
  core_nodes_version : "1.27.4-gke.900",
  notebook_nodes_version : "1.27.4-gke.900",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

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

user_buckets = {}
