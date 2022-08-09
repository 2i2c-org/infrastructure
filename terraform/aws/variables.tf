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
  type        = map(object({ delete_after : number }))
  default     = {}
  description = <<-EOT
  S3 Buckets to be created.

  The key for each entry will be prefixed with {var.prefix}- to form
  the name of the bucket.

  The value is a map, with 'delete_after' the only accepted key in that
  map - it lists the number of days after which any content in the
  bucket will be deleted. Set to null to not delete data.
  EOT
}

variable "hub_cloud_permissions" {
  type        = map(object({ requestor_pays : bool, bucket_admin_access : set(string), extra_iam_policy : string }))
  default     = {}
  description = <<-EOT
  Map of cloud permissions given to a particular hub

  Key is name of the hub namespace in the cluster, and values are particular
  permissions users running on those hubs should have. Currently supported are:

  1. requestor_pays: Identify as coming from the google cloud project when accessing
     storage buckets marked as  https://cloud.google.com/storage/docs/requester-pays.
     This *potentially* incurs cost for us, the originating project, so opt-in.
  2. bucket_admin_access: List of S3 storage buckets that users on this hub should have read
     and write permissions for.
  3. extra_iam_policy: An AWS IAM Policy document that grants additional rights to the users
     on this hub when talking to AWS services.
  EOT
}

variable "extra_user_iam_policy" {
  default     = {}
  description = <<-EOT
  Policy JSON to attach to the IAM role assumed by users of the hub.

  Used to grant additional permissions to the IAM role that is assumed by
  user pods when making requests to AWS services (such as S3)
  EOT
}

variable "db_instance_class" {
  default     = "db.t3.micro"
  description = <<-EOT
  EOT
}

variable "db_storage_size" {
  default     = 10
  description = <<-EOT
  EOT
}

variable "db_engine" {
  default     = "mysql"
  description = <<-EOT
  EOT
}


variable "db_engine_version" {
  default     = "8.0"
  description = <<-EOT
  EOT
}

variable "db_instance_identifier" {
  description = <<-EOT
  EOT
}




