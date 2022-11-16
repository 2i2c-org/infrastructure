# This template assumes a multi-tenant cluster

prefix                 = "{{ cluster_name }}"
project_id             = "{{ cluster_name }}"

zone                   = "{{ cluster_zone }}"
region                 = "{{ cluster_region }}"

# Default to a HA cluster for reliability
regional_cluster = true

core_node_machine_type = "n1-highmem-4"

# For multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore       = true
filestore_capacity_gb  = 1024

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : core_node_machine_type,
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
}

# Config connector is needed on multi-tenant clusters for bucket access 
# Tip: uncomment the line below if this cluster will need buckets and list them below
# config_connector_enabled = true

user_buckets = {}
