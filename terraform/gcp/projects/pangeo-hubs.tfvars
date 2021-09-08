prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
enable_private_cluster = true

core_node_machine_type = "n1-highmem-4"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy    = true

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = true

# Setup nodepools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {"size": "small"}
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {"size": "medium"}
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    labels: {"size": "large"}
  },
  "ml_large" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    labels: {"size": "ml_large"}
  },
}

user_buckets = [
  "pangeo-scratch"
]

enable_filestore = true
