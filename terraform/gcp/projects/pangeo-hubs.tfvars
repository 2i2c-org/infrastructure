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
prefix                 = "pangeo-hubs"
project_id             = "pangeo-integration-te-3eea"
billing_project_id     = "pangeo-integration-te-3eea"
zone                   = "us-central1-b"
region                 = "us-central1"
regional_cluster       = false
core_node_machine_type = "n2-highmem-4"
enable_private_cluster = true

k8s_versions = {
  # NOTE: This isn't a regional cluster / highly available cluster, when
  #       upgrading the control plane, there will be ~5 minutes of k8s not being
  #       available making new server launches error etc.
  min_master_version : "1.29.1-gke.1589018",
  core_nodes_version : "1.29.1-gke.1589018",
  notebook_nodes_version : "1.29.1-gke.1589018",
  dask_nodes_version : "1.29.1-gke.1589018",
}

# Multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for NFS
enable_filestore      = true
filestore_capacity_gb = 4608


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
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
}

hub_cloud_permissions = {
  "staging" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["scratch-staging"],
    hub_namespace : "staging"
  },
  "prod" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["scratch"],
    hub_namespace : "prod"
  },
  "coessing" : {
    allow_access_to_external_requester_pays_buckets : true,
    bucket_admin_access : ["coessing-scratch"],
    hub_namespace : "coessing"
  },
}
