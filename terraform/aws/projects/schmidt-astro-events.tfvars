/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "us-east-1"
cluster_name           = "schmidt-astro-events"
cluster_nodes_location = "us-east-1a"

# Tip: uncomment and verify any missing info in the lines below if you want
#       to setup scratch buckets for the hubs on this cluster.
#

ebs_volumes = {
"staging" = {
    name_suffix = "staging",
    type        = "gp3",
    size        = 10,
    tags        = {
      "2i2c:hub-name" : "staging",
      "JHCM:HubName": "staging"
    },
  },
"workshop" = {
    name_suffix = "workshop",
    type        = "gp3",
    size        = 100,
    tags        = {
      "2i2c:hub-name" : "workshop"
      "JHCM:HubName": "staging"
    },
  },

}
enable_nfs_backup = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : {
      "2i2c:hub-name" : "staging"
      "JHCM:HubName": "staging"
    },
  },

  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : {
      "2i2c:hub-name" : "workshop",
      "JHCM:HubName": "workshop"
    },
  },
}


hub_cloud_permissions = {
 "staging" : {
   bucket_admin_access : ["scratch-staging"],
 },
 "workshop" : {
   bucket_admin_access : ["scratch-workshop"],
 },
}

enable_jupyterhub_cost_monitoring = true