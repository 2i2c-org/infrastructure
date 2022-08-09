region = "us-west-2"

cluster_name = "allen-swdb"

cluster_nodes_location = "us-west-2a"

db_enabled = true
db_engine = "mysql"
db_engine_version = "8.0"
db_instance_identifier = "swdb"
db_storage_size = 200

user_buckets = {
    "scratch-staging": {
        "delete_after" : 7
    },
    "scratch": {
        "delete_after": 7
    },
}


hub_cloud_permissions = {
  "staging" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch-staging"],
    extra_iam_policy: ""
  },
  "prod" : {
    requestor_pays: true,
    bucket_admin_access: ["scratch"],
    extra_iam_policy: ""
  },
}