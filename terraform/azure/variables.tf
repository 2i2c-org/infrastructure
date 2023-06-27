variable "subscription_id" {
  type        = string
  description = <<-EOT
  Subscription ID inside which to create our resources

  This is the unit of billing.
  `az account list -o table` shows the list of subscriptions you
  have access to after you login with `az login`.
  EOT
}

variable "tenant_id" {
  type        = string
  description = <<-EOT
  Tenant ID inside which our subscription is housed

  `az account show -s SUBSCRIPTION_ID -o table` will show the ID of the tenant
  after you have logged in with `az login`.
  EOT
}

variable "resourcegroup_name" {
  type        = string
  description = <<-EOT
  Name of resource group that will hold cluster & other resources
  EOT
}

variable "location" {
  type        = string
  default     = "westus2"
  description = <<-EOT
  Data center where all our resources will be located.

  `az account list-locations -o table` will give you the
  available list.
  EOT
}

variable "kubernetes_version" {
  type        = string
  description = <<-EOT
  Version of kubernetes the cluster should use.

  `az aks get-versions --location westus2 -o table` will
  display the list of available versions.
  EOT
}


variable "core_node_vm_size" {
  type        = string
  description = <<-EOT
  VM Size to use for core nodes

  Core nodes will always be on, and count as 'base cost'
  for a cluster. We should try to run with as few of them
  as possible.

  WARNING: CHANGING THIS WILL DESTROY AND RECREATE THE CLUSTER!
  EOT
}


variable "global_container_registry_name" {
  type        = string
  description = <<-EOT
  Name of container registry to use for our image.

  This needs to be globally unique across all of Azure (ugh?)
  and not contain dashes or underscores.
  EOT
}

variable "global_storage_account_name" {
  type        = string
  description = <<-EOT
  Name of storage account to use for Azure files

  This needs to be globally unique across all of Azure (ugh?)
  and not contain dashes or underscores.
  EOT
}

variable "ssh_pub_key" {
  type        = string
  description = <<-EOT
  SSH public key that'll be authorized to login to nodes.

  The username is `hub-admin`, and you can use the private key
  associated with this public key to login.
  EOT
}

variable "notebook_nodes" {
  type = map(object({
    min : number,
    max : number,
    vm_size : string,
    labels : optional(map(string), {}),
    taints : optional(list(string), []),
    kubernetes_version : optional(string, "")
  }))
  description = "Notebook node pools to create"
  default     = {}
}

variable "dask_nodes" {
  type = map(object({
    min : number,
    max : number,
    vm_size : string,
    labels : optional(map(string), {}),
    taints : optional(list(string), []),
    kubernetes_version : optional(string, "")
  }))
  description = "Dask node pools to create"
  default     = {}
}

variable "create_service_principal" {
  type        = bool
  default     = false
  description = <<-EOT
  When true, create a Service Principal to authenticate with.

  This is a temporary fix to allow for the fact that we cannot create Service
  Principals for UToronto.
  EOT
}

variable "storage_size" {
  type        = number
  description = <<-EOT
  Size (in GB) of the storage to provision
  EOT
}
