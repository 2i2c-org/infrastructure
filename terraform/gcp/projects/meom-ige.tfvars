prefix     = "meom-ige"
project_id = "meom-ige-cnrs"

zone   = "us-central1-b"
region = "us-central1"

core_node_machine_type = "n1-highmem-2"

# Single-tenant cluster, network policy not needed
enable_network_policy = false

regional_cluster = false

notebook_nodes = {
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

dask_nodes = {
  "small" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-2",
  },
  "medium" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-8",
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16",
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32",
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64",
  },

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
