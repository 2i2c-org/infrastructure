region = "us-west-2"

cluster_name = "openscapeshub"

cluster_nodes_location = "us-west-2b"

default_budget_alert = {
  "enabled" : false,
}

enable_grafana_athena_iam   = true
athena_write_storage_bucket = "openscapes-cost-usage-report"
athena_read_storage_bucket  = "openscapes-2i2c-cur"


# Remove this variable to tag all our resources with {"ManagedBy": "2i2c"}
tags = {}

# The initial EFS is now used by the prod hub only
# So we tag it appropriately for costs purposes
original_single_efs_tags = { "2i2c:hub-name" : "prod" }

filestores = {
  "staging" = {
    name_suffix = "staging"
    tags = {
      "2i2c:hub-name" : "staging"
    }
  }
  "workshop" = {
    name_suffix = "workshop"
    tags = {
      "2i2c:hub-name" : "workshop"
    }
  }
}

user_buckets = {
  "scratch-staging" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "scratch" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "scratch-workshop" : {
    "delete_after" : 7,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
  "prod-homedirs-archive" : {
    "archival_storageclass_after" : 3,
    "delete_after" : 185,
  },
  "persistent-staging" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "staging" },
  },
  "persistent" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "prod" },
  },
  "persistent-workshop" : {
    "delete_after" : null,
    "tags" : { "2i2c:hub-name" : "workshop" },
  },
}


hub_cloud_permissions = {
  "staging" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch-staging",
        "persistent-staging",
      ],
    },
  },
  "prod" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch",
        "persistent",
      ],
    }
  },
  "workshop" : {
    "user-sa" : {
      bucket_admin_access : [
        "scratch-workshop",
        "persistent-workshop",
      ],
    }
  },
}

active_cost_allocation_tags = [
  "2i2c:hub-name",
  "2i2c:node-purpose",
  "aws:eks:cluster-name",
  "kubernetes.io/cluster/{var_cluster_name}",
  "kubernetes.io/created-for/pvc/name",
  "kubernetes.io/created-for/pvc/namespace",
]
