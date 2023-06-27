prefix     = "qcl"
project_id = "qcl-hub"

zone   = "europe-west1-d"
region = "europe-west1"

core_node_machine_type = "n2-highmem-2"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 2048

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  }
}

notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-standard-48",
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n2-standard-96",
  },
  "large-highcpu" : {
    min : 0,
    max : 100,
    machine_type : "n2-highcpu-32",
  },
  "huge-highcpu" : {
    min : 0,
    max : 100,
    machine_type : "n2-highcpu-96",
  }
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : false,
    bucket_admin_access : ["scratch-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : false,
    bucket_admin_access : ["scratch"],
    hub_namespace : "prod"
  }
}

container_repos = []

