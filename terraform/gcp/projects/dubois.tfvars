/*
 Some of the assumptions this template makes about the cluster:
   - multi-tenant with staging & prod hubs
   - regional
   - no scratch buckets support
*/

prefix     = "dubois"
project_id = "dubois-436615"

zone   = "us-central1-b"
region = "us-central1"

# Config required to enable automatic budget alerts to be sent to support@2i2c.org
billing_account_id   = "0157F7-E3EA8C-25AC3C"

enable_network_policy = true

k8s_versions = {
 min_master_version : "1.30.4-gke.1348000",
 core_nodes_version : "1.30.4-gke.1348000",
 notebook_nodes_version : "1.30.4-gke.1348000",
}

core_node_machine_type = "n2-highmem-2"

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#
#user_buckets = {
#  "scratch-staging" : {
#    "delete_after" : 7,
#  },
#  # Tip: add more scratch buckets below, if this cluster will be multi-tenant
#}

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
#hub_cloud_permissions = {
#  "staging" : {
#    allow_access_to_external_requester_pays_buckets : false,
#    bucket_admin_access : ["scratch-staging"],
#    hub_namespace : "staging",
#  },
#  # Tip: add more namespaces below, if this cluster will be multi-tenant
#}

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
