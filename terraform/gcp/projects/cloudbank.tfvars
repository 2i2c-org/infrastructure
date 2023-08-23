prefix     = "cb"
project_id = "cb-1003-1696"

zone   = "us-central1-b"
region = "us-central1"

core_node_machine_type = "n1-highmem-4"

enable_filestore      = true
filestore_capacity_gb = 1024

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

regional_cluster = false

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4"
  },
}

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16"
  },
}

user_buckets = {}
