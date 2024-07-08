prefix                = "latam"
project_id            = "catalystproject-392106"
region                = "southamerica-east1"
zone                  = "southamerica-east1-c"
enable_network_policy = true

# This is the average of total costs for Apr -> Jun 2024 +20% in USD
budget_alert_amount = "1672"
billing_account_id  = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
}

filestores = {
  filestore = {
    name_suffix = null,
    capacity_gb = 6144,
    tier        = "BASIC_HDD"
  },
  filestore_b = {
    name_suffix = "b",
    capacity_gb = 2048,
    tier        = "BASIC_HDD"
  }
}

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
  // Created as part of "LEAP"-style method of data input/output as per:
  // https://github.com/2i2c-org/infrastructure/issues/4214
  "persistent-unam" : {
    "delete_after" : null,
    "extra_admin_members" : [
      "group:persistent-unam-writers@2i2c.org"
    ]
  },
}

hub_cloud_permissions = {
  "unam" : {
    bucket_admin_access : ["scratch-unam", "persistent-unam"],
    hub_namespace : "unam",
  },
}
