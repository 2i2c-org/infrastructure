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
