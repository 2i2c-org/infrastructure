prefix                   = "dubois"
project_id               = "dubois-436615"
zone                     = "us-central1-b"
region                   = "us-central1"
enable_network_policy    = true
enable_filestore_backups = true
core_node_machine_type   = "n2-highmem-2"
filestores               = {}

# Config required to enable automatic budget alerts to be sent to support@2i2c.org
billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.32.1-gke.1200003",
  core_nodes_version : "1.32.1-gke.1200003",
  notebook_nodes_version : "1.32.1-gke.1200003",
}

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
