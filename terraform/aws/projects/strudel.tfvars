/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "us-west-2"
cluster_name           = "strudel"
cluster_nodes_location = "us-west-2a"

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
#    "user-sa" : {
#      bucket_admin_access : ["scratch-staging"],
#    },
#  },
#  # Tip: add more namespaces below, if this cluster will be multi-tenant
#}