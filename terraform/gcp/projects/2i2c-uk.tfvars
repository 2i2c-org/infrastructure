prefix     = "two-eye-two-see-uk"
project_id = "two-eye-two-see-uk"

zone   = "europe-west2-b"
region = "europe-west2"

billing_account_id  = "0157F7-E3EA8C-25AC3C"
budget_alert_amount = "500"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  "n2-highmem-4-b" : {
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
  },
}

user_buckets = {}
