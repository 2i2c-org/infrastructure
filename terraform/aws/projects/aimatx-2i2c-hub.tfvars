/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "us-west-2"
cluster_name           = "aimatx-2i2c-hub"
cluster_nodes_location = "us-west-2a"

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#

ebs_volumes = {
  "staging" = {
    name_suffix = "staging",
    type        = "gp3",
    size        = 10,
    tags        = { "2i2c:hub-name" : "staging" },
  },
  "prod" = {
    name_suffix = "prod",
    type        = "gp3",
    size        = 100,
    tags        = { "2i2c:hub-name" : "prod" },
  },

}
enable_nfs_backup = true

user_buckets = {

  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch-prod" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" },
  }
}

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup specific cloud permissions for the buckets in this cluster.
#
hub_cloud_permissions = {

  "staging" : {
    bucket_admin_access : ["scratch-staging", "persistent-staging"],
  },

  "prod" : {
    bucket_admin_access : ["scratch-prod", "persistent"],
  },
}

# Uncomment to enable cost monitoring
enable_jupyterhub_cost_monitoring = true
