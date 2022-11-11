prefix                 = "leap"
project_id             = "leap-pangeo"
core_node_machine_type = "n1-highmem-4"

# No need for this to be a private cluster, public ones are cheaper
enable_private_cluster = false

# GPUs not available in us-central1-b
zone             = "us-central1-c"
region           = "us-central1"
regional_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  }
  # For https://github.com/2i2c-org/infrastructure/issues/1230#issuecomment-1278183441
  "persistent" : {
    "delete_after" : null
  },
  "persistent-staging" : {
    "delete_after" : null
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
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
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
  "small" : {
    min : 0,
    max : 200,
    machine_type : "n1-highmem-2",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "medium" : {
    min : 0,
    max : 200,
    machine_type : "n1-highmem-4",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "large" : {
    min : 0,
    max : 200,
    machine_type : "n1-highmem-8",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "huge" : {
    min : 0,
    max : 200,
    machine_type : "n1-highmem-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
}
