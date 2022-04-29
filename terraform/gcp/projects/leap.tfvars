prefix                 = "leap"
project_id             = "leap-pangeo"
core_node_machine_type = "n1-highmem-4"

# No need for this to be a private cluster, public ones are cheaper
enable_private_cluster = false

# GPUs not available in us-central1-b
zone = "us-central1-c"
region = "us-central1"
regional_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore = true
filestore_capacity_gb = 1024

user_buckets = [
  "scratch-staging",
  "scratch"
]

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch-staging"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access: ["scratch"],
    hub_namespace: "prod"
  }
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
  "gpu-k80" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels: {},
    gpu: {
      enabled: true,
      type: "nvidia-tesla-k80",
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
