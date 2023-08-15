prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

zone   = "us-central1-b"
region = "us-central1"

core_node_machine_type = "n1-highmem-4"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

regional_cluster = false

enable_filestore      = true
filestore_capacity_gb = 3584

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
  },
  "climatematch" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-32",
    labels : {
      "2i2c.org/community" : "climatematch"
    },
    taints : [{
      key : "2i2c.org/community",
      value : "climatematch",
      effect : "NO_SCHEDULE"
    }],
    resource_labels : {
      "community" : "climatematch"
    },
  },
  # Nodepool for neurohackademy. Tracking issue: https://github.com/2i2c-org/infrastructure/issues/2681
  "neurohackademy" : {
    # We expect around 120 users
    min : 0,
    max : 100,
    machine_type : "n1-highmem-16",
    labels : {
      "2i2c.org/community" : "neurohackademy"
    },
    taints : [{
      key : "2i2c.org/community",
      value : "neurohackademy",
      effect : "NO_SCHEDULE"
    }],
    resource_labels : {
      "community" : "neurohackademy"
    },
  }
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
  }
}

user_buckets = {}


hub_cloud_permissions = {
  "dask-staging" : {
    requestor_pays : true,
    bucket_admin_access : [],
    hub_namespace : "dask-staging"
  },
  "ohw" : {
    requestor_pays : true,
    bucket_admin_access : [],
    hub_namespace : "ohw"
  },
  # Can't use full name here as it violates line length restriction of service account id
  "catalyst-coop" : {
    requestor_pays : true,
    bucket_admin_access : [],
    hub_namespace : "catalyst-cooperative"
  },
}

container_repos = [
  "pilot-hubs",
  "binder-staging",
]
