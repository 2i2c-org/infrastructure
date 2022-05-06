prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
core_node_machine_type = "n1-highmem-4"
enable_private_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy  = true

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = false

# Setup a filestore for in-cluster NFS
enable_filestore = true
filestore_capacity_gb = 2048

regional_cluster = false

user_buckets = [
  "scratch",
  "scratch-staging"
]

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {},
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {},
  },
}

dask_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {},
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {},
  },
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch-staging"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch"],
    hub_namespace: "prod"
  },
}