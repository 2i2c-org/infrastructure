prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

core_node_machine_type = "n1-highmem-4"

enable_network_policy    = true
config_connector_enabled = true

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "e2-highmem-4"
  },
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "e2-highmem-4"
  },
}

user_buckets = []
