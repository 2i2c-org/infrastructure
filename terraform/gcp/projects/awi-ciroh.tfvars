prefix                 = "awi-ciroh"
project_id             = "awi-ciroh"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n1-highmem-4"
enable_network_policy  = true
enable_filestore       = true
filestore_capacity_gb  = 1024

user_buckets = {
  "scratch-staging": {
    "delete_after": 7
  },
  "scratch": {
    "delete_after": 7
  },
  "persistent-staging": {
    "delete_after": null
  },
  "persistent": {
    "delete_after": null
  }
}

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 20,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "medium" : {
    min : 15,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "large" : {
    min : 5,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "huge" : {
    min : 5,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
}

dask_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : false,
    bucket_admin_access: ["scratch-staging", "persistent-staging"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : false,
    bucket_admin_access: ["scratch", "persistent"],
    hub_namespace: "prod"
  }
}

container_repos = [ ]
