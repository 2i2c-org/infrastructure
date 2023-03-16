prefix     = "pilot-hubs"
project_id = "two-eye-two-see"

core_node_machine_type = "n1-highmem-4"

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy    = true

regional_cluster = false

# Some hubs want a storage bucket, so we need to have config connector enabled
config_connector_enabled = true

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
    labels: { },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "ohw": {
    min: 1,
    max: 100,
    machine_type: "n1-highmem-8",
    labels: {
      "2i2c.org/community": "ohw"
    },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  }
}

dask_nodes = {
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n1-highmem-4",
    labels: { },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
  "ohw": {
    min: 0,
    max: 100,
    machine_type: "n1-highmem-4",
    labels: {
      "2i2c.org/community": "ohw"
    },
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  }
}

user_buckets = { }


hub_cloud_permissions = {
  "dask-staging" : {
    requestor_pays : true,
    bucket_admin_access: [],
    hub_namespace: "dask-staging"
  },
  "ohw" : {
    requestor_pays : true,
    bucket_admin_access: [],
    hub_namespace: "ohw"
  },
  # Can't use full name here as it violates line length restriction of service account id
  "catalyst-coop" : {
    requestor_pays : true,
    bucket_admin_access: [],
    hub_namespace: "catalyst-cooperative"
  },
}

container_repos = [
  "pilot-hubs",
  "binder-staging",
]
