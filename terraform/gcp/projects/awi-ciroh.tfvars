prefix                 = "awi-ciroh"
project_id             = "ciroh-jupyterhub-423218"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
#core_node_machine_type = "n4-highmem-4"
enable_network_policy = true
enable_logging        = false

core_node_boot_disk = {
  #type = "hyperdisk-balanced"
}

enable_filestore_backups = true
filestores               = {}

single_process_oom_kill = false

persistent_disks = {
  "staging" = {
    size        = 165 # in GiB
    name_suffix = "staging"
  }
  "prod" = {
    size        = 2965 # in GiB
    name_suffix = "prod"
  }
  "workshop" = {
    size        = 1000 # in GiB
    name_suffix = "workshop"
  }
}

# Cloud costs for this project are not passed through by 2i2c
budget_alert_enabled = false
billing_account_id   = ""

k8s_versions = {
  min_master_version : "1.35.3-gke.1943000",
  core_nodes_version : "1.35.3-gke.1943000",
  notebook_nodes_version : "1.35.3-gke.1943000",
  dask_nodes_version : "1.35.3-gke.1943000",
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
  "scratch-workshop" : {
    "delete_after" : 7,
    "uniform_bucket_level_access_only" : true
  },
}

# Setup notebook node pools
notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "n2-highmem-16-a" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  },
  "n2-standard-16" : {
    min : 0,
    # Keep the numbers down, for safety!
    max : 100,
    machine_type : "n2-standard-16",
  },
  "n2-standard-64" : {
    min : 0,
    # Keep the numbers down, for safety!
    max : 20,
    machine_type : "n2-standard-64",
  },

  # Workshop N4 nodes
  # Designed around n4-standard-16 node configuration
  # These are optimal for supporting even huge instances whilst 
  # Having better perf on hyperdisks than 64
  # Model this on Medium profiles
  # Assuming 10GiB scratch per user, 240MiB/s, 1250 IOPS
  "n4-standard-4" : {
    min : 0,
    # Keep the numbers down, for safety!
    max : 100,
    machine_type : "n4-standard-4",

    disk_type : "hyperdisk-balanced",

    # Prefer large disks as cheap and safer
    disk_size_gb : 130,

    # Bump these relative to scaling from 64, as the law of large numbers is worse for smaller samples
    # And the pathological best-case is objectively worse (one person using IO can only hit disk limit)
    # than the n4-standard-64 case
    # Minimum 3000  
    disk_iops : 3000,
    # Limit of n4-standard-4
    disk_throughput : 240
  },
  "n4-standard-16" : {
    min : 0,
    # Keep the numbers down, for safety!
    max : 100,
    machine_type : "n4-standard-16",

    disk_type : "hyperdisk-balanced",

    # Allow for 50% oversubscription (small + medium) and 100GiB for images
    # i.e. X = (X_user * N_user * 1.5) + 100
    disk_size_gb : 160,

    # Do not compute oversubscription due to small numbers --
    # Mix of smaller-than-medium profiles would disrupt this
    disk_iops : 7000,
    disk_throughput : 1200
  },
  "n4-standard-64" : {
    min : 0,
    # Keep the numbers down, for safety!
    max : 30,
    machine_type : "n4-standard-64",

    disk_type : "hyperdisk-balanced",
    disk_size_gb : 340,

    # Limit of n4-standard-64 is 2400 MiB/s
    disk_iops : 15000,
    disk_throughput : 2400,
  },

  "gpu-t4" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-8",

    # Use regular storage for scratch
    # As this is an n1 node
    disk_type : "pd-ssd",
    disk_size_gb : 100,

    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1,
    },
    zones : [
      # Get GPUs wherever they are available, as sometimes a single
      # zone might be out of GPUs.
      "us-central1-a",
      "us-central1-b",
      "us-central1-c",
      "us-central1-f"
    ]
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
  "workshop" : {
    bucket_admin_access : ["scratch-workshop"],
    hub_namespace : "workshop"
  }
}

container_repos = []
