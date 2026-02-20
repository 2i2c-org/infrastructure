prefix                 = "hhmi"
project_id             = "hhmi-398911"
zone                   = "us-west2-b"
region                 = "us-west2"
core_node_machine_type = "n2-highmem-4"
billing_account_id     = "0157F7-E3EA8C-25AC3C"
enable_network_policy  = true

k8s_versions = {
  min_master_version : "1.32.1-gke.1357001",
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
  dask_nodes_version : "1.32.1-gke.1357001",
}

# Disable single centralised filestore in favour of persistent disks
filestores = {}

persistent_disks = {
  "spyglass" = {
    size        = 60 # in GB
    name_suffix = "spyglass"
  }
}

hub_cloud_permissions = {
  "binder" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : [],
    hub_namespace : "binder"
  }
}

user_buckets = {}

# Setup a single node pool, as we don't offer resource selection dropdowns here
notebook_nodes = {
  "n2-highmem-2" : {
    min : 0,
    max : 10, # Capped at 10 rather than 100
    machine_type : "n2-highmem-2",
    zones : [
      # us-west2 has limited resources, so lots of resource exhaustion
      "us-west2-a",
      "us-west2-b",
      "us-west2-c",
    ]
  }
}
