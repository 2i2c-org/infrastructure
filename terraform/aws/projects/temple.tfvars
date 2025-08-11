/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "us-west-2"
cluster_name           = "temple"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 100 # in GB 
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
}

# "scratch-staging" : {
#   "delete_after" : 7,
#   "tags" : { "2i2c:hub-name" : "staging" },
# },

# "scratch-prod" : {
#   "delete_after" : 7,
#   "tags" : { "2i2c:hub-name" : "prod" },
# },


# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
# hub_cloud_permissions = {

#  "staging" : {
#    bucket_admin_access : ["scratch-staging"],
#  },

#  "prod" : {
#    bucket_admin_access : ["scratch-prod"],
#  },


# Uncomment the lines below to Enable cost allocation tags
# for standalone AWS accounts

# active_cost_allocation_tags = [
#   "2i2c:hub-name",
#   "2i2c.org/cluster-name",
#   "alpha.eksctl.io/cluster-name",
#   "kubernetes.io/cluster/{var_cluster_name}",
#   "kubernetes.io/created-for/pvc/namespace",
# ]

