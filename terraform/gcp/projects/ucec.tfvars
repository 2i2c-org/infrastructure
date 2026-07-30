/*
 Some of the assumptions this template makes about the cluster:
   - multi-tenant with staging & prod hubs
   - regional
   - no scratch buckets support
*/

prefix     = "ucec"
project_id = "ucec-503914"

zone   = "us-central1-b"
region = "us-central1"

filestores = {}

# Config required to enable automatic budget alerts to be sent to support@2i2c.org
budget_alert_enabled = true
billing_account_id   = "0157F7-E3EA8C-25AC3C"

single_process_oom_kill = false

k8s_versions = {
  min_master_version : "1.35.3-gke.1943000",
  core_nodes_version : "1.35.3-gke.1943000",
  notebook_nodes_version : "1.35.3-gke.1943000",
}

core_node_machine_type = "n2-highmem-2"
enable_network_policy  = true

persistent_disks = {
  "staging" = {
    size        = 1 # in GB
    name_suffix = "staging"
  },
  "prod" = {
    size        = 100 # in GB
    name_suffix = "prod"
  }
}

notebook_nodes = {
  "n2-highmem-4" : {
    min : 0,
    max : 8,
    machine_type : "n2-highmem-4",
  },
  #  "n2-highmem-16" : {
  #    min : 0,
  #    max : 100,
  #    machine_type : "n2-highmem-16",
  #  },
  #  "n2-highmem-64" : {
  #    min : 0,
  #    max : 100,
  #    machine_type : "n2-highmem-64",
  #  },
  #  "gpu-t4" : {
  #    min : 0,
  #    max : 100,
  #    machine_type : "n1-standard-8",
  #    gpu : {
  #      enabled : true,
  #      type : "nvidia-tesla-t4",
  #      count : 1
  #    },
  #    zones : [
  #      # Get GPUs wherever they are available, as sometimes a single
  #      # zone might be out of GPUs.
  #      "us-central1-a",
  #      "us-central1-b",
  #      "us-central1-c",
  #      "us-central1-f"
  #    ]
  #  },
}



user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "usage_logs" : true,
  },
  "scratch" : {
    "delete_after" : 7,
    "usage_logs" : true,
  }
  "persistent" : {
    "delete_after" : null,
    "usage_logs" : true,
  },
  "persistent-staging" : {
    "delete_after" : null,
    "usage_logs" : true,
  }
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    bucket_admin_access : ["scratch", "persistent"],
    hub_namespace : "prod"
  }
}
