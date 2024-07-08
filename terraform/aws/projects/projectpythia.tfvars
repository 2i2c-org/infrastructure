region = "us-west-2"

cluster_name = "projectpythia"

cluster_nodes_location = "us-west-2a"

default_budget_alert = {
  "enabled" : false,
}

# Remove this variable to tag all our resources with {"ManagedBy": "2i2c"}
tags = {}

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#
#user_buckets = {
#  "scratch-" : {
#    "delete_after" : 7
#  },
# Tip: add more scratch buckets below, if this cluster will be multi-tenant
#}

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
#hub_cloud_permissions = {
#  "" : {
#    "user-sa" : {
#      bucket_admin_access : ["scratch-"],
#    },
#  },
# # Tip: add more namespaces below, if this cluster will be multi-tenant
#}