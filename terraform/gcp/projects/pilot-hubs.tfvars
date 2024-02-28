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
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : [],
    hub_namespace : "dask-staging"
  },
  "ohw" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : [],
    hub_namespace : "ohw"
  },
  # Can't use full name here as it violates line length restriction of service account id
  "catalyst-coop" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : [],
    hub_namespace : "catalyst-cooperative"
  },
  "jackeddy" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["jackeddy-scratch"],
    hub_namespace : "jackeddy"
  },
}

container_repos = [
  "pilot-hubs",
  "binder-staging",
  "agu-binder"
]
