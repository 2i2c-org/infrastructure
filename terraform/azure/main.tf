
terraform {
  required_version = "~> 1.9"
  required_providers {
    azurerm = {
      # ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest
      source  = "hashicorp/azurerm"
      version = "~> 4.3"
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

# ref: https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.jupyterhub.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.jupyterhub.kube_config[0].cluster_ca_certificate)
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

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_registry
resource "azurerm_container_registry" "container_registry" {
  count = var.create_container_registry ? 1 : 0

  name                = var.global_container_registry_name
  resource_group_name = azurerm_resource_group.jupyterhub.name
  location            = azurerm_resource_group.jupyterhub.location
  sku                 = "Premium"
  admin_enabled       = true
}

locals {
  registry_creds = {
    "imagePullSecret" = try({
      "username" : azurerm_container_registry.container_registry[0].admin_username,
      "password" : azurerm_container_registry.container_registry[0].admin_password,
      "registry" : "https://${azurerm_container_registry.container_registry[0].login_server}"
    }, null)
  }
  storage_threshold = var.storage_size * var.fileshare_alert_available_fraction
}

output "registry_creds_config" {
  value     = var.create_container_registry ? jsonencode(local.registry_creds) : null
  sensitive = true
}
