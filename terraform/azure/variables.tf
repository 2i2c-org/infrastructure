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

variable "kubernetes_rbac_enabled" {
  type        = bool
  default     = true
  description = <<-EOT
  Enable RBAC enforcement on kubernetes clusters.

  New clusters **must** have this set to true. Set to false
  only for existing clusters so they are not recreated
  unnecessarily.
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

variable "cluster_sku_tier" {
  type        = string
  default     = "Free"
  description = <<-EOT
  Support tier to be used for this cluster

  https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers
  has more information.

  Can be one of "Free" | "Standard" | "Premium".

  Defaults to "Free", as that's mostly good enough for our use cases.
  EOT
}

variable "node_pools" {
  type = map(
    list(
      object({
        name : string,
        vm_size : string,
        os_disk_size_gb : optional(number, 100),
        kubelet_disk_type : optional(string, "Temporary"),
        min : number,
        max : number,
        labels : optional(map(string), {}),
        taints : optional(list(string), []),
        kubernetes_version : optional(string, ""),
      })
    )
  )
  description = <<-EOT
  Node pools to create to be listed under the keys 'core', 'user', and 'dask'.

  There should be exactly one core node pool. The core node pool is given a
  special treatment by being listed directly in the cluster resource's
  'default_node_pool' field.
  EOT

  validation {
    condition     = length(var.node_pools["core"]) == 1
    error_message = "The core node pool is mapped to the cluster resource's `default_node_pool`, due to this we require exactly one core node pool to be specified."
  }

  validation {
    condition     = length(setsubtract(keys(var.node_pools), ["core", "user", "dask"])) == 0
    error_message = "Only three kinds of node pools supported: 'core', 'user', and 'dask'."
  }

  validation {
    condition     = length(setintersection(keys(var.node_pools), ["core", "user", "dask"])) == 3
    error_message = "All three kinds of node pools ('core', 'user', and 'dask') must be declared, even if they are empty lists of node pools."
  }
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
  Size (in GB) of the storage to provision.

  Minimum is 100
  EOT
}

variable "fileshare_alert_available_fraction" {
  type        = number
  default     = 0.9
  description = <<-EOT
  Decimal fraction (between 0 and 1) of total space available in fileshare. If used space is over this, we fire an alert to pagerduty.
  EOT
}

variable "budget_alert_enabled" {
  type        = bool
  default     = false
  description = <<-EOT
  Enable budget alerts. Disable in cases where we do not have enough permissions
  on the billing account or cloud account to enable APIs.
  EOT
}

variable "budget_alert_amount" {
  type        = string
  description = <<-EOT
  Amount of *forecasted spend* at which to send a billing alert. Current practice
  is to set this to the average of the last 3 months expenditure + 20%.
  EOT
}