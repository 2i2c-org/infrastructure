/*
 Some of the assumptions this template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/

region = "us-west-2"

cluster_name = "kitware"

cluster_nodes_location = "us-west-2a"

# Tip: uncomment and fill the missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#
user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7
  },
  "scratch" : {
    "delete_after" : 7
  },
}

hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : ""
  },
  "prod" : {
    bucket_admin_access : ["scratch"],
    extra_iam_policy : ""
  },
}