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
      archival_storageclass_after : optional(number, null),
      tags : optional(map(string), {}),
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
  3. `tags` - bucket specific tags to be merged into the general tags variable.
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
  Cloud permissions attached to Kubernetes Service Accounts in a particular
  k8s namespace (hub) in this cluster.

  The key is a Kubernetes namespace, which by convention in 2i2c clusters
  is also the name of the hub.

  The value is itself a map, as each hub can have multiple Kubernetes Service
  Accounts attached to it, for different kinds of users. The key is the name
  of the Kubernetes Service Account. By convention, basehub currently only
  supports creation of Kubernetes Service Accounts `user-sa` (for non-admin
  users on the hub). The value can be one of:

  1. bucket_admin_access: List of S3 storage buckets to grant full read & write
     permissions to.
  2. bucket_readonly_access: List of S3 storage buckets to grant full read
     permissions to.
  3. extra_iam_policy: An AWS IAM Policy document that grants additional rights
     to this Kubernetes Service Account.

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

variable "default_tags" {
  type = map(string)
  default = {
    "2i2c.org/cluster-name" = "{var_cluster_name}"
    "ManagedBy"             = "2i2c"
  }
  description = <<-EOT
  Default tags to apply to all resources created. The value is an object as we may
  wish to apply multiple tags.

  Current tags are:

  1. ManagedBy: This tag will indicate who manages the deployed resource. By
     default, this will be set to "2i2c". This helps communities who bring their
     own billing account distinguish between resources 2i2c manages, and those
     they deploy and manage themselves.
  2. 2i2c.org/cluster-name: helps clarify that a resource is associated with the
     creation of a specific cluster, which can help if a cluster is re-created or
     multiple clusters would be deployed.
  EOT
}

variable "default_budget_alert" {
  type = object({
    enabled : optional(bool, true)
    subscriber_email_addresses : optional(
      list(string),
      ["support+{var_cluster_name}@2i2c.org"]
    )
  })
  default     = {}
  description = <<-EOT
  A boilerplate budget alert initially setup for AWS accounts we pay the bill for.
  EOT
}

variable "disable_cluster_wide_filestore" {
  default     = true
  type        = bool
  description = <<-EOT
  Whether or not the initial cluster-wide `homedirs` filestore
  should be disabled and deleted.

  Should be set to true once an EFS instance per cluster has been
  setup and all the relevant data has been migrated.
  EOT
}

variable "original_single_efs_tags" {
  default     = {}
  type        = map(string)
  description = <<-EOT
  Extra tags to apply to the original cluster wide EFS
  EOT
}

variable "filestores" {
  type = map(object({
    name_suffix : optional(string, null),
    tags : optional(map(string), {}),
  }))
  default = {
  }
  description = <<-EOT
  Deploy one or more AWS ElasticFileStores for home directories.

  This provisions a managed NFS solution that can be mounted as
  home directories for users. If this is not enabled, a manual or
  in-cluster NFS solution must be set up.

  - name-suffix: Suffix to append to the name of the FileStore. This
    prevents name-clashing. Default: null.

  - tags: Tags to apply to the homedir. The value is an object as we
    are appending existing tags to homedir specific tags.
    We use CamelCase for tag names to match AWS's tagging style.
    Default tag is:
      1. Name: This tag will indicate the name of the homedir.
        By default, this will be set to "hub-homedirs-{name_suffix}".
  EOT
}

variable "active_cost_allocation_tags" {
  type    = list(string)
  default = []

  description = <<-EOT
  Tags to be treated as active cost allocation tags.

  Without permissions on the billing account, we get the following
  error if we try to use this:

      Failed to update Cost Allocation Tag:
      Linked account doesn't have access to cost allocation tags.

  Due to that, we don't provide a default value here, but if we could,
  we would want to activate at least the following that are relevant
  to cost attribution currently as piloted by the openscapes cluster:

  - 2i2c:hub-name
  - 2i2c.org/cluster-name
  - alpha.eksctl.io/cluster-name
  - kubernetes.io/cluster/{var_cluster_name}

  Cost allocation tags can only be activated after sufficient amount of
  time has passed since resources was tagged, so expect a few hours or
  up to 24 hours in order you can activate them without running into
  this error:

      Failed to update Cost Allocation Tag:
      Tag keys not found: 2i2c.org/cluster-name
  EOT
}

variable "enable_aws_ce_grafana_backend_iam" {
  type        = bool
  default     = false
  description = <<-EOT
  Create an IAM role with attached policy to permit read use of AWS Cost Explorer API.
  EOT
}

variable "ebs_volumes" {
  type = map(object({
    size        = number
    type        = string
    name_suffix = optional(string, null)
    tags        = optional(map(string), {})
  }))
  default     = {}
  description = <<-EOT
  Deploy one or more AWS ElasticBlockStore volumes.

  This provisions a managed EBS volume that can be used by jupyterhub-home-nfs
  server to store home directories for users.
  EOT
}

variable "enable_nfs_backup" {
  type        = bool
  default     = false
  description = <<-EOT
  Enable backup of NFS home directories using Data Lifecycle Manager (DLM).
  EOT
}
