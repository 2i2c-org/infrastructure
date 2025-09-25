/*
 Some of the assumptions this jinja2 template makes about the cluster:
   - location of the nodes of the kubernetes cluster will be <region>a
   - no default scratch buckets support
*/
region                 = "us-west-2"
cluster_name           = "heliophysics"
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
    size        = 400,
    tags        = { "2i2c:hub-name" : "prod" },
  },

}
enable_nfs_backup = true

budget_alerts = {
  # Per https://github.com/2i2c-org/meta/issues/2523,
  # they have two major events, between Sep 22-26 and
  # Oct 19-24. We don't have custom time'd budgets yet, so let's
  # use monthly budgets of $1000 for now.
  "monthly" : {
    time_period = "MONTHLY",
    emails = [
      # "yuvipanda@2i2c.org",
      "shawn.polson@lasp.colorado.edu"
    ],
    max_cost = 1000
  },
}
monthly_budget_alerts = {

}
# "scratch-staging" : {
#   "delete_after" : 7,
#   "tags" : { "2i2c:hub-name" : "staging" },
# },

# "scratch-prod" : {
#   "delete_after" : 7,
#   "tags" : { "2i2c:hub-name" : "prod" },
# },


hub_cloud_permissions = {
  "staging" : {
    bucket_admin_access : [],
  },

  "prod" : {
    bucket_admin_access : [],
  }
}

default_budget_alert = {
  enabled : false
}

# Uncomment to enable cost monitoring
enable_jupyterhub_cost_monitoring = true