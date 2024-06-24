prefix                 = "awi-ciroh"
project_id             = "ciroh-jupyterhub-423218"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true
enable_filestore       = true
filestore_capacity_gb  = 2560
enable_logging         = false

k8s_versions = {
  min_master_version : "1.29.4-gke.1043002",
  core_nodes_version : "1.29.4-gke.1043002",
  notebook_nodes_version : "1.29.4-gke.1043002",
  dask_nodes_version : "1.29.4-gke.1043002",
}

# FIXME: Enable these buckets once the access policy restriction has been lifted
#        on the project
# user_buckets = {
#   "scratch-staging" : {
#     "delete_after" : 7
#   },
#   "scratch" : {
#     "delete_after" : 7
#   },
#   "persistent-staging" : {
#     "delete_after" : null
#   },
#   "persistent" : {
#     "delete_after" : null
#   }
# }

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

# FIXME: Uncomment requester pays lines and add bucket names to admin access
#        once bucket access policy restriction has been lifted from the project
hub_cloud_permissions = {
  "staging" : {
    # allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : [],
    hub_namespace : "staging"
  },
  "prod" : {
    # allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : [],
    hub_namespace : "prod"
  }
}

container_repos = []
