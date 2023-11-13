# SETTING UP TO WORK WITH THIS FILE:
# -------------------------------------------------------------------------------
#
# The terraform state associated with this file is stored in a dedicated GCP
# bucket, so a new terraform backend has to be chosen. Also, you will need to
# authenticate with a @columbia.edu account as our @2i2c.org accounts don't have
# access.
#
# This can look something like this:
#
#     gcloud auth login --update-adc
#
#     cd terraform/gcp
#     rm -rf .terraform
#
#     terraform init -backend-config backends/pangeo-backend.hcl
#     terraform workspace select pangeo-hubs
#
#     terraform apply --var-file projects/pangeo-hubs.tfvars
#
# FIXME: core_node_machine_type should be set to n2-highmem-4 as its enough
prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
billing_project_id     = "pangeo-integration-te-3eea"
zone                   = "us-central1-b"
region                 = "us-central1"
core_node_machine_type = "n2-highmem-8"
enable_private_cluster = true

k8s_versions = {
  min_master_version : "1.26.5-gke.2100",
  core_nodes_version : "1.26.4-gke.1400",
  notebook_nodes_version : "1.26.4-gke.1400",
  dask_nodes_version : "1.26.4-gke.1400",
}

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for NFS
enable_filestore      = true
filestore_capacity_gb = 4608

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
  "small" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-2",
  },
  "medium" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-4",
  },
  "large" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-8",
  },
  "huge" : {
    min : 0,
    max : 100,
    machine_type : "n1-standard-16",
  },
}

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  # FIXME: Rename this to "n2-highmem-16" when given the chance and no such nodes are running
  "worker" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
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
