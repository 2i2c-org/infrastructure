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
  GCS Buckets to be created.

  The key for each entry will be prefixed with {var.prefix}- to form
  the name of the bucket.

  The value is a map, with 'delete_after' the only accepted key in that
  map - it lists the number of days after which any content in the
  bucket will be deleted. Set to null to not delete data.
  EOT
}

variable "hub_cloud_permissions" {
  type        = map(object({ requestor_pays : bool, bucket_admin_access : set(string) }))
  default     = {}
  description = <<-EOT
  Map of cloud permissions given to a particular hub

  Key is name of the hub namespace in the cluster, and values are particular
  permissions users running on those hubs should have. Currently supported are:

  1. requestor_pays: Identify as coming from the google cloud project when accessing
     storage buckets marked as  https://cloud.google.com/storage/docs/requester-pays.
     This *potentially* incurs cost for us, the originating project, so opt-in.
  2. bucket_admin_access: List of GCS storage buckets that users on this hub should have read
     and write permissions for.
  EOT
}
