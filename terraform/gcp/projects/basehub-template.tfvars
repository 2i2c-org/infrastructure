/*
 Some of the assumptions this template makes about the cluster:
   - multi-tenant with staging & prod hubs
   - regional
   - no scratch buckets support
*/

prefix     = "{{ cluster_name }}"
project_id = "{{ project_id }}"

zone   = "{{ cluster_region }}"
region = "{{ cluster_region }}"

# Default to a HA cluster for reliability
regional_cluster = true

core_node_machine_type = "n2-highmem-2"

# For multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    labels : {},
    gpu : {
      # Tip: use this flag to enable GPU on this machine type
      # if there is GPU availability in the chosen the zone
      enabled : false,
      type : "",
      count : 0
    }
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
}

# Config connector is needed on multi-tenant clusters for bucket access 
# Tip: uncomment the line below if this cluster will need buckets and list them below
# config_connector_enabled = true

user_buckets = {}
