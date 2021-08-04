prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

core_node_machine_type = "n1-highmem-4"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy    = true

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = true

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "e2-highmem-4",
    labels: { }
  },
  "ohw": {
    min: 0,
    max: 50,
    machine_type: "n1-highmem-4",
    labels: {
      "2i2c.org/community": "ohw"
    },
  }
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "e2-highmem-4",
    labels: { }
  },
  "ohw": {
    min: 0,
    max: 100,
    machine_type: "n1-highmem-4",
    labels: {
      "2i2c.org/community": "ohw"
    },
  }
}

user_buckets = []
