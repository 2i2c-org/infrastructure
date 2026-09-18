prefix             = "two-eye-two-see-uk"
project_id         = "two-eye-two-see-uk"
zone               = "europe-west2-b"
region             = "europe-west2"
billing_account_id = "0157F7-E3EA8C-25AC3C"

# Explicitly disable filestore in favour of persistent disks
filestores = {}

k8s_versions = {
  min_master_version : "1.35.3-gke.1943000",
  core_nodes_version : "1.35.3-gke.1943000",
  notebook_nodes_version : "1.35.3-gke.1943000",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

notebook_nodes = {
  # To be deleted when empty
  "n2-highmem-4" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    node_version : "1.34.4-gke.1130000",
    taints : [
      # Prevent new pods from scheduling here.
      {
        key : "manual-phaseout"
        value : "noop"
        effect : "NO_SCHEDULE"
      }
    ],
  },
  "n2-highmem-4-a" : {
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
}

user_buckets = {}

persistent_disks = {
  "staging" = {
    size        = 10 # in GB
    name_suffix = "staging"
  },
  "lis" = {
    size        = 570 # in GB
    name_suffix = "lis"
  }
}
