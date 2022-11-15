prefix                 = "{{ cluster_name }}"
project_id             = "{{ cluster_name }}"

zone                   = "{{ cluster_region }}-b"
region                 = "{{ cluster_region }}"

core_node_machine_type = "n1-highmem-4"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore       = true
filestore_capacity_gb  = 1024

# No plans to provide storage buckets to users on this hub, so no need to deploy config connector
config_connector_enabled = false

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

user_buckets = {}
