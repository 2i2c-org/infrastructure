prefix     = "leap"
project_id = "leap-pangeo"
# core_node_machine_type is set to n2-highmem-4 instead of n2-highmem-2 because
# prometheus requires more memory than a n2-highmem-2 can provide.
core_node_machine_type = "n2-highmem-4"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
  dask_nodes_version : "1.29.1-gke.1589018",
}

# GPUs not available in us-central1-b
zone   = "us-central1-c"
region = "us-central1"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 3072

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "extra_admin_members" : [],
    "usage_logs" : true,
  },
  "scratch" : {
    "delete_after" : 7,
    "extra_admin_members" : [],
    "usage_logs" : true,
  }
  # For https://github.com/2i2c-org/infrastructure/issues/1230#issuecomment-1278183441
  "persistent" : {
    "delete_after" : null,
    "extra_admin_members" : ["group:leap-persistent-bucket-writers@googlegroups.com"],
    "usage_logs" : true,
  },
  "persistent-staging" : {
    "delete_after" : null,
    "extra_admin_members" : ["group:leap-persistent-bucket-writers@googlegroups.com"],
    "usage_logs" : true,
  }
  # For https://github.com/2i2c-org/infrastructure/issues/1230#issuecomment-1278183441
  "persistent-ro" : {
    "delete_after" : null,
    "extra_admin_members" : ["group:leap-persistent-bucket-writers@googlegroups.com"],
    "usage_logs" : true,
  },
  "persistent-ro-staging" : {
    "delete_after" : null,
    "extra_admin_members" : ["group:leap-persistent-bucket-writers@googlegroups.com"],
    "usage_logs" : true,
  }
}

hub_cloud_permissions = {
  "staging" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    bucket_readonly_access : ["persistent-ro-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["scratch", "persistent"],
    bucket_readonly_access : ["persistent-ro"],
    hub_namespace : "prod"
  }
}

# Setup notebook node pools
notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  # FIXME: tainted, to be deleted when empty, replaced by k8s upgraded variant
  "n2-highmem-16" : {
    # A minimum of one is configured for LEAP to ensure quick startups at all
    # time. Cost is not a greater concern than optimizing startup times.
    min : 1,
    max : 100,
    machine_type : "n2-highmem-16",
    node_version : "1.27.4-gke.900",
  },
  "n2-highmem-16-b" : {
    # A minimum of one is configured for LEAP to ensure quick startups at all
    # time. Cost is not a greater concern than optimizing startup times.
    min : 1,
    max : 100,
    machine_type : "n2-highmem-16",
    node_version : "1.27.4-gke.900",
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64"
  }
  # FIXME: tainted, to be deleted when empty, replaced by k8s upgraded variant
  "gpu-t4" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    node_version : "1.27.4-gke.900",
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1
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
  "gpu-t4-b" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1
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
    # Disable preemptive nodes for dask so we can remove possible complications
    # on why some dask computations are dying off.
    # See https://github.com/2i2c-org/infrastructure/issues/2396
    preemptible : false,
    machine_type : "n2-highmem-16"
  },
}
