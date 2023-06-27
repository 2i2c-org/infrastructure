/*
 Some of the assumptions this template makes about the cluster:
   - single-tenant with staging & prod hubs
   - regional
   - scratch buckets support
*/

prefix     = "{{ cluster_name }}"
project_id = "{{ project_id }}"

zone   = "{{ cluster_region }}"
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
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  # Tip: add more scratch buckets below, if this cluster will be multi-tenant
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
  # Tip: add more namespaces below, if this cluster will be multi-tenant
}

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  },
}

dask_nodes = {
  "medium" : {
    min : 0,
    max : 200,
    machine_type : "n2-highmem-16",
  },
}
