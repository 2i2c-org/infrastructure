region = "{{ cluster_region }}"

cluster_name = "{{ cluster_name }}"

cluster_nodes_location = "{{ cluster_region }}a"

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
    requestor_pays : true,
    bucket_admin_access : ["scratch-staging"],
    extra_iam_policy : ""
  },
  "prod" : {
    requestor_pays : true,
    bucket_admin_access : ["scratch"],
    extra_iam_policy : ""
  },
}
