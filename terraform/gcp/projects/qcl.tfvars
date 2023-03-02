prefix                 = "qcl"
project_id             = "qcl-hub"

zone                   = "europe-west1-d"
region                 = "europe-west1"

core_node_machine_type = "n2-highmem-2"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore       = true
filestore_capacity_gb  = 2048

user_buckets = {
  "scratch-staging": {
    "delete_after": 7
  },
  "scratch": {
    "delete_after": 7
  }
}

notebook_nodes = {
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
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
    machine_type : "n2-highmem-16",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "very-large-highcpu" : {
    min : 0,
    max : 100,
    machine_type : "n2-highcpu-32",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "huge-highcpu" : {
    min : 0,
    max : 100,
    machine_type : "n2-highcpu-96",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : false,
    bucket_admin_access: ["scratch-staging"],
    hub_namespace: "staging"
  },
  "prod" : {
    requestor_pays : false,
    bucket_admin_access: ["scratch"],
    hub_namespace: "prod"
  }
}

container_repos = [ ]

