prefix     = "hhmi"
project_id = "hhmi-398911"

zone   = "us-west2-b"
region = "us-west2"

core_node_machine_type = "n2-highmem-4"

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.32.1-gke.1357001",
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
  dask_nodes_version : "1.32.1-gke.1357001",
}

enable_network_policy    = true
enable_filestore_backups = true

persistent_disks = {
  "staging" = {
    size        = 40 # in GB
    name_suffix = "staging"
  },
  "prod" = {
    size        = 100 # in GB
    name_suffix = "prod"
  }
}

hub_cloud_permissions = {
  "binder" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : [],
    hub_namespace : "binder"
  }
}

user_buckets = {}

# Setup notebook node pools
notebook_nodes = {
  "n2-highmem-4" : {
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
  }
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
    machine_type : "n2-highmem-16",
  },
}