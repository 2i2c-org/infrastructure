prefix                 = "awi-ciroh"
project_id             = "awi-ciroh"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true
enable_filestore       = true
filestore_capacity_gb  = 1024

k8s_versions = {
  min_master_version : "1.25.8-gke.500",
  core_nodes_version : "1.25.6-gke.1000",
  notebook_nodes_version : "1.25.6-gke.1000",
  dask_nodes_version : "1.25.6-gke.1000",
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  "persistent-staging" : {
    "delete_after" : null
  },
  "persistent" : {
    "delete_after" : null
  }
}

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4"
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16"
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64"
  },
}

dask_nodes = {
  "medium" : {
    min : 0,
    max : 200,
    machine_type : "n2-highmem-16"
  },
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : false,
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : false,
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
}

container_repos = []
