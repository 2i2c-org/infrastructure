prefix     = "qcl"
project_id = "qcl-hub"

zone             = "europe-west1-d"
region           = "europe-west1"
regional_cluster = true

k8s_versions = {
  min_master_version : "1.27.4-gke.900",
  core_nodes_version : "1.27.4-gke.900",
  notebook_nodes_version : "1.27.4-gke.900",
}

# FIXME: Remove temp_opt_out_node_purpose_label_core_nodes when a node upgrade can be
#        done. See https://github.com/2i2c-org/infrastructure/issues/3405.
temp_opt_out_node_purpose_label_core_nodes = true

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
  # FIXME: Remove temp_opt_out_node_purpose_label when a node upgrade can be
  #        done. See https://github.com/2i2c-org/infrastructure/issues/3405.
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    temp_opt_out_node_purpose_label : true,
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
  }
  "n2-standard-48" : {
    min : 0,
    max : 100,
    machine_type : "n2-standard-48",
  },
  "n2-standard-96" : {
    min : 0,
    max : 100,
    machine_type : "n2-standard-96",
  },
  "n2-highcpu-32" : {
    min : 0,
    max : 100,
    machine_type : "n2-highcpu-32",
  },
  "n2-highcpu-96" : {
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

