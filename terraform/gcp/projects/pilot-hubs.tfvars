prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  # NOTE: This isn't a regional cluster / highly available cluster, when
  #       upgrading the control plane, there will be ~5 minutes of k8s not being
  #       available making new server launches error etc.
  min_master_version : "1.32.1-gke.1357001",
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
  dask_nodes_version : "1.32.1-gke.1357001",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

filestores = {
  "filestore" : {
    capacity_gb : 5120,
    source_backup : "projects/two-eye-two-see/locations/us-central1/backups/test",
  },
}
enable_filestore_backups = true

persistent_disks = {
  "staging" = {
    size        = 5 # in GB
    name_suffix = "staging"
  },
  "dask-staging" = {
    size        = 3 # in GB
    name_suffix = "dask-staging"
  },
  "imagebuilding-demo" = {
    size        = 10 # in GB
    name_suffix = "imagebuilding-demo"
  },
  "demo" = {
    size        = 2 # in GB
    name_suffix = "demo"
  },
  "mtu" = {
    size        = 75 # in GB
    name_suffix = "mtu"
  },
  "temple" = {
    size        = 1300 # in GB
    name_suffix = "temple"
  },
  "ucmerced-staging" = {
    size        = 10 # in GB
    name_suffix = "ucmerced-staging"
  },
  "ucmerced" = {
    size        = 120 # in GB
    name_suffix = "ucmerced"
  }
}

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
    max : 100,
    machine_type : "n2-highmem-16",
  },
}

user_buckets = {
  "scratch-dask-staging" : {
    "delete_after" : 7,
  },
}


hub_cloud_permissions = {
  "dask-staging" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["scratch-dask-staging"],
    hub_namespace : "dask-staging",
  },
}

container_repos = [
  "binder-staging",
  "binderhub-ui-demo"
]
