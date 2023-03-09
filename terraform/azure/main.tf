
terraform {
  required_providers {
    azurerm = {
      # ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest
      #
      # FIXME: v3 has been released and we are still at v2, see release notes:
      #        https://github.com/hashicorp/terraform-provider-azurerm/releases/tag/v3.0.0
      #
      source = "hashicorp/azurerm"
      version = "~> 2.99"
    }

    azuread = {
      # ref: https://registry.terraform.io/providers/hashicorp/azuread/latest
      source = "hashicorp/azuread"
      version = "~> 2.35"
    }
  }
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

provider "azuread" {
  tenant_id = var.tenant_id
}
provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}

resource "azurerm_resource_group" "jupyterhub" {
  name     = var.resourcegroup_name
  location = var.location
}

resource "azurerm_virtual_network" "jupyterhub" {
  name                = "k8s-network"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  address_space       = ["10.0.0.0/8"]
}

resource "azurerm_subnet" "node_subnet" {
  name                 = "k8s-nodes-subnet"
  virtual_network_name = azurerm_virtual_network.jupyterhub.name
  resource_group_name  = azurerm_resource_group.jupyterhub.name
  address_prefixes     = ["10.1.0.0/16"]

  // Create a Service Endpoint to talk to NFS
  service_endpoints = ["Microsoft.Storage"]
}

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.jupyterhub.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config.0.cluster_ca_certificate)
}


resource "azurerm_kubernetes_cluster" "jupyterhub" {
  name                = "hub-cluster"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  kubernetes_version  = var.kubernetes_version
  dns_prefix          = "k8s"

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

  # Core node-pool
  default_node_pool {
    name       = "core"
    node_count = 1
    # Unfortunately, changing anything about VM type / size recreates *whole cluster
    vm_size             = var.core_node_vm_size
    os_disk_size_gb     = 40
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 10
    vnet_subnet_id      = azurerm_subnet.node_subnet.id
    node_labels = {
      "hub.jupyter.org/node-purpose" = "core",
      "k8s.dask.org/node-purpose"    = "core"
    }

    orchestrator_version = var.kubernetes_version
  }

  auto_scaler_profile {
    skip_nodes_with_local_storage = true
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    # I don't trust Azure CNI
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
}



resource "azurerm_kubernetes_cluster_node_pool" "user_pool" {
  for_each = var.notebook_nodes

  name                  = "nb${each.key}"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.jupyterhub.id
  enable_auto_scaling   = true
  os_disk_size_gb       = 200
  vnet_subnet_id        = azurerm_subnet.node_subnet.id

  orchestrator_version = each.value.kubernetes_version == "" ? var.kubernetes_version : each.value.kubernetes_version

  vm_size = each.value.vm_size
  node_labels = merge({
    "hub.jupyter.org/node-purpose" = "user",
    "k8s.dask.org/node-purpose"    = "scheduler"
    "hub.jupyter.org/node-size"    = each.value.vm_size
  }, each.value.labels)

  node_taints = concat([
    "hub.jupyter.org_dedicated=user:NoSchedule"
  ], each.value.taints)


  min_count = each.value.min
  max_count = each.value.max
}

resource "azurerm_kubernetes_cluster_node_pool" "dask_pool" {
  # If dask_nodes is set, we use that. If it isn't, we use notebook_nodes.
  # This lets us set dask_nodes to an empty array to get no dask nodes
  for_each = var.dask_nodes

  name                  = "dask${each.key}"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.jupyterhub.id
  enable_auto_scaling   = true
  os_disk_size_gb       = 200
  vnet_subnet_id        = azurerm_subnet.node_subnet.id

  orchestrator_version = each.value.kubernetes_version == "" ? var.kubernetes_version : each.value.kubernetes_version

  vm_size = each.value.vm_size
  node_labels = merge({
    "k8s.dask.org/node-purpose" = "worker",
    "hub.jupyter.org/node-size" = each.value.vm_size
  }, each.value.labels)

  node_taints = concat([
    "k8s.dask.org_dedicated=worker:NoSchedule"
  ], each.value.taints)


  min_count = each.value.min
  max_count = each.value.max
}

# AZure container registry

resource "azurerm_container_registry" "container_registry" {
  # meh, only alphanumberic chars. No separators. BE CONSISTENT, AZURE
  name                = var.global_container_registry_name
  resource_group_name = azurerm_resource_group.jupyterhub.name
  location            = azurerm_resource_group.jupyterhub.location
  sku                 = "premium"
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
}


output "kubeconfig" {
  value     = azurerm_kubernetes_cluster.jupyterhub.kube_config_raw
  sensitive = true
}

output "registry_creds_config" {
  value     = jsonencode(local.registry_creds)
  sensitive = true
}
