prefix                = "latam"
project_id            = "catalystproject-392106"
region                = "southamerica-east1"
zone                  = "southamerica-east1-c"
enable_network_policy = true

billing_account_id = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.32.1-gke.1357001",
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
}

persistent_disks = {
  "areciboc3" = {
    size        = 1 # in GiB
    name_suffix = "areciboc3"
  },
  "cabana" = {
    size        = 2 # in GiB
    name_suffix = "cabana"
  },
  "cicada" = {
    size        = 90 # in GiB
    name_suffix = "cicada"
  },
  "gita" = {
    size        = 1 # in GiB
    name_suffix = "gita"
  },
  "iner" = {
    size        = 35 # in GiB
    name_suffix = "iner"
  },
  "labi" = {
    size        = 130 # in GiB
    name_suffix = "labi"
  },
  "nnb-ccg" = {
    size        = 1 # in GiB
    name_suffix = "nnb-ccg"
  },
  "plnc" = {
    size        = 1 # in GiB
    name_suffix = "plnc"
  },
  "staging" = {
    size        = 10 # in GiB
    name_suffix = "staging"
  },
  "unam" = {
    size        = 900 # in GiB
    name_suffix = "unam"
  }
  "unitefa-conicet" = {
    size        = 25 # in GiB
    name_suffix = "unitefa-conicet"
  },
  "uprrp" = {
    size        = 1 # in GiB
    name_suffix = "uprrp"
  },
  "valledellili" = {
    size        = 1 # in GiB
    name_suffix = "valledellili"
  },
}

enable_filestore_backups = true
filestores = {
  "filestore_b" = {
    name_suffix = "b",
    capacity_gb = 2304 # 2.25TiB
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
    max : 50,
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
