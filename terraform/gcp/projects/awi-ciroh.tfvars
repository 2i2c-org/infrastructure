prefix                 = "awi-ciroh"
project_id             = "ciroh-jupyterhub-423218"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true
enable_logging         = false

enable_filestore_backups = true
filestores               = {}

enable_nfs_backup = true
persistent_disks = {
  "staging" = {
    size        = 100 # in GB
    name_suffix = "staging"
  }
  "prod" = {
    size        = 2500 # in GB
    name_suffix = "prod"
  }
}

# Cloud costs for this project are not passed through by 2i2c
budget_alert_enabled = false
billing_account_id   = ""

k8s_versions = {
  min_master_version : "1.32.1-gke.1200003",
  core_nodes_version : "1.32.1-gke.1200003",
  notebook_nodes_version : "1.32.1-gke.1200003",
  dask_nodes_version : "1.32.1-gke.1200003",
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "uniform_bucket_level_access_only" : true
  },
  "scratch" : {
    "delete_after" : 7,
    "uniform_bucket_level_access_only" : true
  },
  "persistent-staging" : {
    "delete_after" : null,
    "uniform_bucket_level_access_only" : true
  },
  "persistent" : {
    "delete_after" : null,
    "uniform_bucket_level_access_only" : true
  }
}

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
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
}

container_repos = []
