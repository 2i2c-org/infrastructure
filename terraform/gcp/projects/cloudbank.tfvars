prefix     = "cb"
project_id = "cb-1003-1696"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

k8s_versions = {
  min_master_version : "1.27.5-gke.200",
  core_nodes_version : "1.27.5-gke.200",
  notebook_nodes_version : "1.27.5-gke.200",
  dask_nodes_version : "1.27.5-gke.200",
}

# FIXME: n2-highmem-2 is a better fit for cloudbank as they are currently
#        limited by the number of pods per node and don't use dask-gateway
#        that otherwise can make prothemeus server need more memory than a
#        n2-highmem-2 node can provide.
core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  # FIXME: Remove this node pool when unused, its been replaced by the
  #        n2-highmem-4 node pool
  "user" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    node_version : "1.26.4-gke.1400",
    temp_opt_out_node_purpose_label = true,
  },
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

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16"
  },
}

user_buckets = {}
