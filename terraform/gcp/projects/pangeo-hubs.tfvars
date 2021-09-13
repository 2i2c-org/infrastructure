prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
core_node_machine_type = "n1-highmem-4"
enable_private_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy  = true

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = true

# Setup a filestore for in-cluster NFS
enable_filestore = true

# Enable node auto-provisioning
enable_node_autoprovisioning = true

user_buckets = [
  "pangeo-scratch"
]
