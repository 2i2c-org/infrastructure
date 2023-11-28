prefix     = "hhmi"
project_id = "hhmi-398911"

zone   = "us-west2-b"
region = "us-west2"

# Default to a HA cluster for reliability
regional_cluster = true

core_node_machine_type = "n2-highmem-4"

k8s_versions = {
  min_master_version : "1.27.5-gke.200",
  core_nodes_version : "1.27.5-gke.200",
  notebook_nodes_version : "1.27.5-gke.200",
  dask_nodes_version : "1.27.5-gke.200",
}

# Network policy is required to enforce separation between hubs on multi-tenant clusters
# Tip: uncomment the line below if this cluster will be multi-tenant
# enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

user_buckets          = {}
hub_cloud_permissions = {}

# Setup notebook node pools
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

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "n2-highmem-16" : {
    min : 0,
    max : 200,
    machine_type : "n2-highmem-16",
  },
}