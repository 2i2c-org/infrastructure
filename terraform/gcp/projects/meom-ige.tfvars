prefix     = "meom-ige"
project_id = "meom-ige-cnrs"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

k8s_versions = {
  min_master_version : "1.27.4-gke.900",
  core_nodes_version : "1.27.4-gke.900",
  notebook_nodes_version : "1.27.4-gke.900",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = false

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
  "small" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-2"
  },
  "medium" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-8"
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16"
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32"
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64"
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
  }
}

user_buckets = {
  "scratch" : {
    "delete_after" : null
  },
  "data" : {
    "delete_after" : null
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch", "data"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch", "data"],
    hub_namespace : "prod"
  }
}
