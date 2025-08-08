/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "{{ cluster_region }}"
cluster_name           = "{{ cluster_name }}"
cluster_nodes_location = "{{ cluster_region }}a"

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#

{% for hub in hubs %}
filestores = {
  "{{ hub }}" = {
    name_suffix = "{{ hub }}",
    tags        = { "2i2c:hub-name" : "{{ hub }}" },
  },
}
{% endfor %}

{% for hub in hubs %}
# "scratch-{{ hub }}" : {
#   "delete_after" : 7,
#   "tags" : { "2i2c:hub-name" : "{{ hub }}" },
# },
{% endfor %}

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
# hub_cloud_permissions = {
{% for hub in hubs %}
#  "{{ hub }}" : {
#    bucket_admin_access : ["scratch-{{ hub }}"],
#  },
{% endfor %}

# Uncomment if aws.billing.active_cost_tags is true in cluster.yaml
# enable_jupyterhub_cost_monitoring = true
