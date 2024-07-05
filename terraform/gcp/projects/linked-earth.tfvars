prefix     = "linked-earth"
project_id = "linked-earth-hubs"

zone   = "us-central1-c"
region = "us-central1"

# This is the average of total costs for Apr -> Jun 2024 +20% in USD
budget_alert_amount = "540"
billing_account_id  = "018C36-9A47B4-82AE21"

k8s_versions = {
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
  dask_nodes_version : "1.29.1-gke.1589018",
}

core_node_machine_type = "n2-highmem-4"
enable_network_policy  = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  }
}

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
    max : 100,
    machine_type : "n2-highmem-16",
  }
}

hub_cloud_permissions = {
  "staging" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : ["scratch-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    allow_access_to_external_requester_pays_buckets : false,
    bucket_admin_access : ["scratch"],
    hub_namespace : "prod"
  }
}

container_repos = []
