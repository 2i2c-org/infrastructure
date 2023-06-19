prefix     = "two-eye-two-see-uk"
project_id = "two-eye-two-see-uk"

zone   = "europe-west2-b"
region = "europe-west2"

core_node_machine_type = "n1-highmem-4"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4"
  },
}

user_buckets = {}
