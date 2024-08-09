prefix                = "latam"
project_id            = "catalystproject-392106"
region                = "southamerica-east1"
zone                  = "southamerica-east1-c"
enable_network_policy = true

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
}

filestores = {
  "filestore_b" = {
    name_suffix = "b",
    capacity_gb = 2048
  }
}

core_node_machine_type = "n2-highmem-2"

notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
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
  },
  "gpu-t4-highmem-4" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
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
  "scratch-areciboc3" : {
    "delete_after" : 7,
  },
  "scratch-valledellili" : {
    "delete_after" : 7,
  },
}

hub_cloud_permissions = {
  "unam" : {
    bucket_admin_access : ["scratch-unam", "persistent-unam"],
    hub_namespace : "unam",
  },
  "areciboc3" : {
    bucket_admin_access : ["scratch-areciboc3"],
    hub_namespace : "areciboc3",
  },
  "valledellili" : {
    bucket_admin_access : ["scratch-valledellili"],
    hub_namespace : "valledellili",
  },
}
