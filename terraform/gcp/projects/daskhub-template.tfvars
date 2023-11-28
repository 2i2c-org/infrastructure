/*
 Some of the assumptions this template makes about the cluster:
   - single-tenant with staging & prod hubs
   - regional
   - scratch buckets support
*/

prefix     = "{{ cluster_name }}"
project_id = "{{ project_id }}"

zone   = "{{ cluster_region }}-b"
region = "{{ cluster_region }}"

# Default to a HA cluster for reliability
regional_cluster = true

core_node_machine_type = "n2-highmem-4"

# Network policy is required to enforce separation between hubs on multi-tenant clusters
# Tip: uncomment the line below if this cluster will be multi-tenant
# enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

user_buckets = {
  "scratch-{{ hub_name }}" : {
    "delete_after" : 7
  },
  # Tip: add more scratch buckets below, if this cluster will be multi-tenant
}

hub_cloud_permissions = {
  "{{ hub_name }}" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-{{ hub_name }}"],
    hub_namespace : "{{ hub_name }}"
  },
  # Tip: add more namespaces below, if this cluster will be multi-tenant
}

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
