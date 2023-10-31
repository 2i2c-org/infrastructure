prefix     = "qcl"
project_id = "qcl-hub"

zone             = "europe-west1-d"
region           = "europe-west1"
regional_cluster = true

k8s_versions = {
  min_master_version : "1.25.10-gke.2700",
  core_nodes_version : "1.24.9-gke.3200",
  notebook_nodes_version : "1.24.9-gke.3200",
}

core_node_machine_type = "n2-highmem-2"
enable_network_policy  = true

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
  # FIXME: Rename this to "n2-highmem-4" when given the chance and no such nodes are running
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  # FIXME: Rename this to "n2-highmem-16" when given the chance and no such nodes are running
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  # FIXME: Rename this to "n2-highmem-48" when given the chance and no such nodes are running
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n2-standard-48",
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  }
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

