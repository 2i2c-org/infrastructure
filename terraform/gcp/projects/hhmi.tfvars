prefix     = "hhmi"
project_id = "hhmi-398911"

zone   = "us-west2-b"
region = "us-west2"

core_node_machine_type = "n2-highmem-4"

# This is the average of total costs for Apr -> Jun 2024 +20% in USD
budget_alert_amount = "797"
billing_account_id  = "0157F7-E3EA8C-25AC3C"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589020",
  core_nodes_version : "1.29.1-gke.1589020",
  notebook_nodes_version : "1.29.1-gke.1589020",
  dask_nodes_version : "1.29.1-gke.1589020",
}

# Network policy is required to enforce separation between hubs on multi-tenant clusters
# Tip: uncomment the line below if this cluster will be multi-tenant
# enable_network_policy  = true

hub_cloud_permissions = {
  "binder" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : [],
    hub_namespace : "binder"
  }
}

user_buckets = {}

# Setup notebook node pools
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
  }
}

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "n2-highmem-16" : {
    min : 0,
    max : 200,
    machine_type : "n2-highmem-16",
  },
}