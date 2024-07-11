prefix     = "two-eye-two-see-uk"
project_id = "two-eye-two-see-uk"

zone   = "europe-west2-b"
region = "europe-west2"

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

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
