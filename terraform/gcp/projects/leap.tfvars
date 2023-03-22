prefix                 = "leap"
project_id             = "leap-pangeo"
# core_node_machine_type is set to n2-highmem-4 instead of n2-highmem-2 because
# prometheus requires more memory than a n2-highmem-2 can provide.
core_node_machine_type = "n2-highmem-4"

k8s_versions = {
  min_master_version: "1.25.6-gke.1000",
  core_nodes_version: "1.25.6-gke.1000",
  notebook_nodes_version: "1.25.6-gke.1000",
  dask_nodes_version: "1.25.6-gke.1000",
}

# GPUs not available in us-central1-b
zone             = "us-central1-c"
region           = "us-central1"
regional_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 2048

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "extra_admin_members": []
  },
  "scratch" : {
    "delete_after" : 7,
    "extra_admin_members": []
  }
  # For https://github.com/2i2c-org/infrastructure/issues/1230#issuecomment-1278183441
  "persistent" : {
    "delete_after" : null,
    "extra_admin_members": ["group:leap-external-bucket-users@2i2c.org"]
  },
  "persistent-staging" : {
    "delete_after" : null,
    "extra_admin_members": ["group:leap-external-bucket-users@2i2c.org"]
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
}

# Setup notebook node pools
notebook_nodes = {
  "medium" : {
    # A minimum of one is configured for LEAP to ensure quick startups at all
    # time. Cost is not a greater concern than optimizing startup times.
    min : 1,
    max : 100,
    machine_type : "n2-highmem-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "gpu-t4" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels : {},
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1
    }
  },
}

dask_nodes = {
  "medium" : {
    min : 0,
    max : 200,
    # Disable preemptive nodes for dask so we can remove possible complications
    # on why some dask computations are dying off.
    # See https://github.com/2i2c-org/infrastructure/issues/2396
    preemptible: false,
    machine_type : "n2-highmem-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
}
