prefix     = "cb"
project_id = "cb-1003-1696"

core_node_machine_type = "n1-highmem-4"

enable_network_policy    = true
config_connector_enabled = false

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
