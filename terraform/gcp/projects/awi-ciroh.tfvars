billing_account_id = "0157F7-E3EA8C-25AC3C"
budget_alert_amount = "800"

prefix                 = "awi-ciroh"
project_id             = "awi-ciroh"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true
enable_filestore       = true
filestore_capacity_gb  = 2560

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
  dask_nodes_version : "1.29.1-gke.1589018",
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
  "n2-highmem-4-b" : {
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
  },
  "gpu-t4" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-8",
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1,
    },
  },
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
    machine_type : "n2-highmem-16"
  },
}

hub_cloud_permissions = {
  "staging" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
}

container_repos = []
