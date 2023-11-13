prefix     = "cb"
project_id = "cb-1003-1696"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

k8s_versions = {
  min_master_version : "1.26.5-gke.2100",
  core_nodes_version : "1.26.5-gke.2100",
  notebook_nodes_version : "1.26.4-gke.1400",
}

# FIXME: Remove temp_opt_out_node_purpose_label when a node upgrade can be
#        done. See https://github.com/2i2c-org/infrastructure/issues/3405.
temp_opt_out_node_purpose_label_core_nodes = true

# FIXME: Transition to n2-highmem-4 when possible
core_node_machine_type = "n1-highmem-4"
enable_network_policy  = true

enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  # FIXME: Update the machine type to "n2-highmem-4" and rename this node pool
  #        when given the chance and no such nodes are running.
  # FIXME: Remove temp_opt_out_node_purpose_label when a node upgrade can be
  #        done. See https://github.com/2i2c-org/infrastructure/issues/3405.
  "user" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    temp_opt_out_node_purpose_label = true
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
