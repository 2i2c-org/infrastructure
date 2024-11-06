region                 = "us-west-2"
cluster_name           = "opensci"
cluster_nodes_location = "us-west-2a"

enable_aws_ce_grafana_backend_iam = true

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch-sciencecore" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "sciencecore" },
  },
  "persistent-sciencecore" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "sciencecore" },
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-staging"],
    },
  },
  "sciencecore" : {
    "user-sa" : {
      bucket_admin_access : ["scratch-sciencecore"],
      bucket_readonly_access : ["persistent-sciencecore"],
    },
    "admin-sa" : {
      bucket_admin_access : ["scratch-sciencecore", "persistent-sciencecore"],
    },
  },
}
