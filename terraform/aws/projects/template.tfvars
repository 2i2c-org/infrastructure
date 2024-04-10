/*
 Some of the assumptions this template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/

region = "{{ cluster_region }}"

cluster_name = "{{ cluster_name }}"

cluster_nodes_location = "{{ cluster_region }}a"

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#
#user_buckets = {
#  "scratch-{{ hub_name }}" : {
#    "delete_after" : 7
#  },
# Tip: add more scratch buckets below, if this cluster will be multi-tenant
#}

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
#hub_cloud_permissions = {
#  "{{ hub_name }}" : {
#    "user-sa" : {
#      bucket_admin_access : ["scratch-{{ hub_name }}"],
#      extra_iam_policy : "",
#    },
#  },
# # Tip: add more namespaces below, if this cluster will be multi-tenant
#}
