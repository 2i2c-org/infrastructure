prefix                 = "leap"
project_id             = "leap-pangeo"
core_node_machine_type = "n1-highmem-4"

# No need for this to be a private cluster, public ones are cheaper
enable_private_cluster = false

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore = true
filestore_capacity_gb = 1024

user_buckets = [
  "scratch-staging",
  "scratch"
]

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
  }
}

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {}
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {}
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {}
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {}
  },
}

dask_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {}
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {}
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {}
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {}
  },
}
