prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
enable_private_cluster = true

core_node_machine_type = "n1-highmem-4"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy    = true

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = true

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4"
    labels : {}
  },
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4"
    labels : {}
  },
}

user_buckets = [
  "pangeo-scratch"
]
