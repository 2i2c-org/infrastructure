region                 = "us-west-2"
cluster_name           = "oceanhackweek"
cluster_nodes_location = "us-west-2a"

ebs_volumes = {
  "staging" = {
    size        = 1
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  },
  "prod" = {
    size        = 100
    type        = "gp3"
    name_suffix = "prod"
    tags        = { "2i2c:hub-name" : "prod" }
  },
}

enable_nfs_backup = true

budget_alerts = {
  "monthly" : {
    time_period = "MONTHLY",
    emails = [
      "emiliomayorga@gmail.com"
    ],
    # They have a total of $1000, and two events (one in Oct, one in Nov) to spend it on
    max_cost = 500
  },
}

# Setup IAM creds but no buckets
hub_cloud_permissions = {
  "staging" : {
  },
  "prod" : {
  }
}