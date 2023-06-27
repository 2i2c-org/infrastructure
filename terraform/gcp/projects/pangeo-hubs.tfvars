prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-4"
enable_private_cluster = true

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 4096

regional_cluster = false


user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
  "coessing-scratch" : {
    "delete_after" : 14
  }
}

# Setup notebook node pools
notebook_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
}

dask_nodes = {
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
    labels : {},
    gpu : {
      enabled : false,
      type : "",
      count : 0
    }
  },
}

hub_cloud_permissions = {
  "staging" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch"],
    hub_namespace : "prod"
  },
  "coessing" : {
    requestor_pays : true,
    bucket_admin_access : ["coessing-scratch"],
    hub_namespace : "coessing"
  },
}
