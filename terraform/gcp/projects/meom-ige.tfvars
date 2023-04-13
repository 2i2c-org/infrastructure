prefix     = "meom-ige"
project_id = "meom-ige-cnrs"

zone       = "us-central1-b"
region     = "us-central1"

core_node_machine_type = "n1-highmem-2"

# Single-tenant cluster, network policy not needed
enable_network_policy    = false

regional_cluster = false

notebook_nodes = {
  "small" : {
    min : 0,
    max : 20,
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
    max : 20,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64",
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
    max : 20,
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
    max : 20,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },

}

user_buckets = {
  "scratch": {
    "delete_after": null
  },
  "scratch-drakkar-demo": {
    "delete_after" : 7
  },
  "data": {
    "delete_after": null
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch", "data"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch", "data"],
    hub_namespace: "prod"
  },
  "drakkar-demo" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch-drakkar-demo"],
    hub_namespace: "drakkar-demo"
  }
}