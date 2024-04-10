variable "region" {
  type        = string
  description = <<-EOT
  AWS region to perform all our operations in.
  EOT
}

variable "cluster_name" {
  type        = string
  description = <<-EOT
  Name of the EKS cluster created with eksctl.
  EOT
}

variable "cluster_nodes_location" {
  type        = string
  description = <<-EOT
  Location of the nodes of the kubernetes cluster
  EOT
}

variable "user_buckets" {
  type = map(
    object({
      delete_after : optional(number, null),
      archival_storageclass_after : optional(number, null)
    })
  )
  default     = {}
  description = <<-EOT
  S3 Buckets to be created.

  The key for each entry will be prefixed with {var.prefix}- to form
  the name of the bucket.

  The value is a map, with the following accepted keys:

  1. `delete_after` - number of days after *creation* an object in this
     bucket will be automatically deleted. Set to null to not delete data.
  2. `archival_storageclass_after` - number of days after *creation* an
     object in this bucket will be automatically transitioned to a cheaper,
     slower storageclass for cost savings. Set to null to not transition.
  EOT
}

variable "hub_cloud_permissions" {
  type = map(
    map(
      object({
        bucket_admin_access : optional(set(string), [])
        bucket_readonly_access : optional(set(string), [])
        extra_iam_policy : optional(string, "")
      })
    )
  )
  default     = {}
  description = <<-EOT
  Map of cloud permissions given to a particular hub (k8s namespace) and
  its associated IAM Role's that are 1:1 with k8s ServiceAccounts.

  Currently supported are:

  1. bucket_admin_access: List of S3 storage buckets that the associated aws-iam-role/k8s-service-account should have read
     and write permissions for.
  2. bucket_readonly_access: List of S3 storage buckets that users on this hub should have read
     permissions for.
  3. extra_iam_policy: An AWS IAM Policy document that grants additional rights to the users
     on this hub when talking to AWS services.
  EOT
}

variable "db_enabled" {
  default     = false
  type        = bool
  description = <<-EOT
  Run a database for the hub with AWS RDS
  EOT
}

variable "db_instance_class" {
  default     = "db.t3.micro"
  type        = string
  description = <<-EOT
  Size (memory & CPU) of the db instance to provision.

  See list in https://aws.amazon.com/rds/instance-types/
  EOT
}

variable "db_storage_size" {
  default     = 10
  type        = number
  description = <<-EOT
  Size (in GiB) of storage to provision for the RDS instance
  EOT
}

variable "db_engine" {
  default     = "mysql"
  type        = string
  description = <<-EOT
  AWS RDS database engine to use.

  We should really only support mysql or postgres here, with a
  preference for postgres.
  EOT
}


variable "db_engine_version" {
  default     = "8.0"
  type        = string
  description = <<-EOT
  Version of database engine to provision.

  See https://awscli.amazonaws.com/v2/documentation/api/latest/reference/rds/describe-db-engine-versions.html
  for more info on how to get list of allowed versions.
  EOT
}

variable "db_instance_identifier" {
  default     = "shared-db"
  type        = string
  description = <<-EOT
  Human readable instance name to give the database server.

  This is used in the hostname, but otherwise doesn't have much of
  an effect.
  EOT
}

variable "db_mysql_user_grants" {
  default     = ["SELECT", "SHOW VIEW", "SHOW DATABASES", "PROCESS"]
  type        = list(string)
  description = <<-EOT
  List of privileges to grant the default non-root hub db user if using mysql
  EOT
}

variable "db_params" {
  default     = {}
  type        = map(string)
  description = <<-EOT
  Mapping of parameters to set on the RDS instance.

  This is specific to the type of database (postgres, mysql) being
  used. You can find the list of available options based on
  documentation here: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithDBInstanceParamGroups.html#USER_WorkingWithParamGroups.Listing
  EOT
}

variable "db_user_password_special_chars" {
  default     = true
  type        = bool
  description = <<-EOT
  Set to True if you don't want special characters in generated user password
  EOT
}
