prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

k8s_versions = {
  min_master_version : "1.27.4-gke.900",
  core_nodes_version : "1.27.4-gke.900",
  notebook_nodes_version : "1.27.4-gke.900",
  dask_nodes_version : "1.27.4-gke.900",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

enable_filestore      = true
filestore_capacity_gb = 5120

notebook_nodes = {
  # FIXME: Delete this node pool when its empty, its replaced by n2-highmem-4-b
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    temp_opt_out_node_purpose_label : true,
  },
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
  # Nodepool for neurohackademy. Tracking issue: https://github.com/2i2c-org/infrastructure/issues/2681
  "neurohackademy" : {
    # We expect around 120 users
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
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
  },
  # Nodepool for temple university. https://github.com/2i2c-org/infrastructure/issues/3158
  # FIXME: Delete this node pool when its empty, its replaced by temple-b
  "temple" : {
    # Expecting upto ~120 users at a time
    min : 0,
    max : 100,
    # Everyone gets a 256M guarantee, and n2-highmem-8 has about 60GB of RAM.
    # This fits upto 100 users on the node, as memory guarantee isn't the constraint.
    # This works ok.
    machine_type : "n2-highmem-8",
    node_version : "1.26.4-gke.1400",
    temp_opt_out_node_purpose_label : true,
    labels : {
      "2i2c.org/community" : "temple"
    },
    taints : [{
      key : "2i2c.org/community",
      value : "temple",
      effect : "NO_SCHEDULE"
    }],
    resource_labels : {
      "community" : "temple"
    },
  },
  "temple-b" : {
    # Expecting upto ~120 users at a time
    min : 0,
    max : 100,
    # Everyone gets a 256M guarantee, and n2-highmem-8 has about 60GB of RAM.
    # This fits upto 100 users on the node, as memory guarantee isn't the constraint.
    # This works ok.
    machine_type : "n2-highmem-8",
    labels : {
      "2i2c.org/community" : "temple"
    },
    taints : [{
      key : "2i2c.org/community",
      value : "temple",
      effect : "NO_SCHEDULE"
    }],
    resource_labels : {
      "community" : "temple"
    },
  },
  "agu-binder" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-8",
    node_version : "1.26.4-gke.1400",
    disk_type : "pd-ssd",
    labels : {
      "2i2c.org/community" : "agu-binder"
    },
    taints : [{
      key : "2i2c.org/community",
      value : "agu-binder",
      effect : "NO_SCHEDULE"
    }],
    resource_labels : {
      "community" : "agu-binder"
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
    max : 100,
    machine_type : "n2-highmem-16",
  },
}

user_buckets = {
  "jackeddy-scratch" : {
    "delete_after" : 7
  }
}


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
  "jackeddy" : {
    requestor_pays : true,
    bucket_admin_access : ["jackeddy-scratch"],
    hub_namespace : "jackeddy"
  },
}

container_repos = [
  "pilot-hubs",
  "binder-staging",
  "agu-binder"
]
