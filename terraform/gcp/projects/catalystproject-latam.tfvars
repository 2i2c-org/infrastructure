prefix                = "latam"
project_id            = "catalystproject-392106"
region                = "southamerica-east1"
zone                  = "southamerica-east1-c"
enable_network_policy = true

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
}

enable_filestore      = true
filestore_capacity_gb = 6144

core_node_machine_type = "n2-highmem-2"

notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    # Per https://github.com/2i2c-org/infrastructure/issues/4213
    disk_size_gb : 400,
  },
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
    # Per https://github.com/2i2c-org/infrastructure/issues/4213
    disk_size_gb : 400,
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
    # Per https://github.com/2i2c-org/infrastructure/issues/4213
    disk_size_gb : 400,
  },
  "gpu-t4-highmem-4" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
    # Per https://github.com/2i2c-org/infrastructure/issues/4213
    disk_size_gb : 400,
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1,
    },
  },
  "gpu-t4-highmem-16" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-16",
    # Per https://github.com/2i2c-org/infrastructure/issues/4213
    disk_size_gb : 400,
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 4,
    },
  },
}

user_buckets = {
  // unam's scratch bucket was setup for James Munroe specifically to copy misc
  // data over for the community (https://2i2c.freshdesk.com/a/tickets/1588)
  "scratch-unam" : {
    "delete_after" : 7,
  },
}

hub_cloud_permissions = {
  "unam" : {
    bucket_admin_access : ["scratch-unam"],
    hub_namespace : "unam",
  },
}
