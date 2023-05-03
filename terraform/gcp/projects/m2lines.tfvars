prefix                 = "m2lines"
project_id             = "m2lines-hub"
core_node_machine_type = "n1-highmem-4"

enable_network_policy  = true

# GPUs not available in us-central1-b
zone = "us-central1-c"
region = "us-central1"
regional_cluster = true

# Setup a filestore for in-cluster NFS
enable_filestore = true
filestore_capacity_gb = 2048

user_buckets = {
  "scratch-staging": {
    "delete_after": 7
  },
  "scratch": {
    "delete_after": 7
  },
  # For https://2i2c.freshdesk.com/a/tickets/218
  "persistent": {
    "delete_after": null
  },
  "persistent-staging": {
    "delete_after": null
  },
  "public-persistent": {
    "delete_after": null
  },

}

# Setup notebook node pools
notebook_nodes = {
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
  "gpu-t4" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: true,
      type: "nvidia-tesla-t4",
      count: 1
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
    requestor_pays : true,
    bucket_admin_access: ["scratch-staging", "persistent-staging"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch", "persistent", "public-persistent"],
    hub_namespace: "prod"
  },
}

bucket_public_access = [
  "public-persistent"
]
