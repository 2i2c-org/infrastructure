
terraform {
  required_version = "~> 1.9"
  required_providers {
    azurerm = {
      # FIXME: upgrade to v4, see https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/4.0-upgrade-guide
      # ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest
      source  = "hashicorp/azurerm"
      version = "~> 3.111"
    }

    azuread = {
      # ref: https://registry.terraform.io/providers/hashicorp/azuread/latest
      source  = "hashicorp/azuread"
      version = "~> 2.53"
    }

    kubernetes = {
      # ref: https://registry.terraform.io/providers/hashicorp/kubernetes/latest
      source  = "hashicorp/kubernetes"
      version = "~> 2.32"
    }

    # Used to decrypt sops encrypted secrets containing PagerDuty keys
    sops = {
      # ref: https://registry.terraform.io/providers/carlpett/sops/latest
      source  = "carlpett/sops"
      version = "~> 1.1"
    }
  }
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

# ref: https://registry.terraform.io/providers/hashicorp/azuread/latest/docs#argument-reference
provider "azuread" {
  tenant_id = var.tenant_id
}

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs#argument-reference
provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/resource_group
resource "azurerm_resource_group" "jupyterhub" {
  name     = var.resourcegroup_name
  location = var.location
}

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_network
resource "azurerm_virtual_network" "jupyterhub" {
  name                = "k8s-network"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  address_space       = ["10.0.0.0/8"]
}

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/subnet
resource "azurerm_subnet" "node_subnet" {
  name                 = "k8s-nodes-subnet"
  virtual_network_name = azurerm_virtual_network.jupyterhub.name
  resource_group_name  = azurerm_resource_group.jupyterhub.name
  address_prefixes     = ["10.1.0.0/16"]

  // Create a Service Endpoint to talk to NFS
  service_endpoints = ["Microsoft.Storage"]
}

# ref: https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.jupyterhub.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].cluster_ca_certificate)
}


# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster
resource "azurerm_kubernetes_cluster" "jupyterhub" {
  name                = "hub-cluster"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  kubernetes_version  = var.kubernetes_version
  dns_prefix          = "k8s"

  role_based_access_control_enabled = var.kubernetes_rbac_enabled

  # "Free" (the default) not supported in westeurope
  sku_tier = var.cluster_sku_tier

  lifecycle {
    # An additional safeguard against accidentally deleting the cluster.
    # The databases for the hubs are held in PVCs managed by the cluster,
    # so cluster deletion will cause data loss!
    prevent_destroy = true
  }

  linux_profile {
    admin_username = "hub-admin"
    ssh_key {
      key_data = var.ssh_pub_key
    }
  }

  auto_scaler_profile {
    skip_nodes_with_local_storage = true
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    # Azure CNI is the default, but we don't trust it to be reliable, so we've
    # opted to use kubenet instead
    network_plugin = "kubenet"
    network_policy = "calico"
  }

  dynamic "service_principal" {
    for_each = var.create_service_principal ? [1] : []

    content {
      client_id     = azuread_service_principal.service_principal[0].object_id
      client_secret = azuread_service_principal_password.service_principal_password[0].value
    }
  }

  # default_node_pool must be set, and it must be a node pool of system type
  # that can't scale to zero. Due to that we are forced to use it, and have
  # decided to use it as our core node pool.
  #
  # Most changes to this node pool forces a replace operation on the entire
  # cluster. This can be avoided with v3.47.0+ of this provider by declaring
  # temporary_name_for_rotation = "coreb".
  #
  # ref: https://github.com/hashicorp/terraform-provider-azurerm/pull/20628
  # ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster#temporary_name_for_rotation.
  #
  default_node_pool {
    name                = var.node_pools["core"][0].name
    vm_size             = var.node_pools["core"][0].vm_size
    os_disk_size_gb     = var.node_pools["core"][0].os_disk_size_gb
    kubelet_disk_type   = var.node_pools["core"][0].kubelet_disk_type
    enable_auto_scaling = true
    min_count           = var.node_pools["core"][0].min
    max_count           = var.node_pools["core"][0].max

    node_labels = merge({
      "hub.jupyter.org/node-purpose" = "core",
      "k8s.dask.org/node-purpose"    = "core"
    }, var.node_pools["core"][0].labels)

    orchestrator_version = coalesce(var.node_pools["core"][0].kubernetes_version, var.kubernetes_version)

    vnet_subnet_id = azurerm_subnet.node_subnet.id
  }
}


# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster_node_pool
resource "azurerm_kubernetes_cluster_node_pool" "user_pool" {
  for_each = { for i, v in var.node_pools["user"] : v.name => v }

  name                = each.value.name
  vm_size             = each.value.vm_size
  os_disk_size_gb     = each.value.os_disk_size_gb
  kubelet_disk_type   = each.value.kubelet_disk_type
  enable_auto_scaling = true
  min_count           = each.value.min
  max_count           = each.value.max

  node_labels = merge({
    "hub.jupyter.org/node-purpose" = "user",
    "k8s.dask.org/node-purpose"    = "scheduler"
  }, each.value.labels)
  node_taints = concat([
    "hub.jupyter.org_dedicated=user:NoSchedule"
  ], each.value.taints)

  orchestrator_version = each.value.kubernetes_version == "" ? var.kubernetes_version : each.value.kubernetes_version

  kubernetes_cluster_id = azurerm_kubernetes_cluster.jupyterhub.id
  vnet_subnet_id        = azurerm_subnet.node_subnet.id
}


# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster_node_pool
resource "azurerm_kubernetes_cluster_node_pool" "dask_pool" {
  for_each = { for i, v in var.node_pools["dask"] : v.name => v }

  name                = each.value.name
  vm_size             = each.value.vm_size
  os_disk_size_gb     = each.value.os_disk_size_gb
  kubelet_disk_type   = each.value.kubelet_disk_type
  enable_auto_scaling = true
  min_count           = each.value.min
  max_count           = each.value.max

  node_labels = merge({
    "k8s.dask.org/node-purpose" = "worker",
  }, each.value.labels)
  node_taints = concat([
    "k8s.dask.org_dedicated=worker:NoSchedule"
  ], each.value.taints)

  orchestrator_version = each.value.kubernetes_version == "" ? var.kubernetes_version : each.value.kubernetes_version

  kubernetes_cluster_id = azurerm_kubernetes_cluster.jupyterhub.id
  vnet_subnet_id        = azurerm_subnet.node_subnet.id
}


# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_registry
resource "azurerm_container_registry" "container_registry" {
  name                = var.global_container_registry_name
  resource_group_name = azurerm_resource_group.jupyterhub.name
  location            = azurerm_resource_group.jupyterhub.location
  sku                 = "Premium"
  admin_enabled       = true
}


locals {
  registry_creds = {
    "imagePullSecret" = {
      "username" : azurerm_container_registry.container_registry.admin_username,
      "password" : azurerm_container_registry.container_registry.admin_password,
      "registry" : "https://${azurerm_container_registry.container_registry.login_server}"
    }
  }
  storage_threshold = var.storage_size * var.fileshare_alert_available_fraction
}

output "kubeconfig" {
  value     = azurerm_kubernetes_cluster.jupyterhub.kube_config_raw
  sensitive = true
}

output "registry_creds_config" {
  value     = jsonencode(local.registry_creds)
  sensitive = true
}
