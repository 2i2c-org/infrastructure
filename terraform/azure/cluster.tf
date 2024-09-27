# This data resource and output provides information on the latest available k8s
# versions supported by Azure Kubernetes Service. This can be used when specifying
# versions to upgrade to via the kubernetes_version variable.
#
# To get the output of relevance, run:
#
#     terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
#
# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/kubernetes_service_versions
data "azurerm_kubernetes_service_versions" "k8s_version_prefixes" {
  location = var.location

  for_each       = var.k8s_version_prefixes
  version_prefix = each.value
}
output "latest_supported_k8s_versions" {
  value = { #data.azurerm_kubernetes_service_versions.current.versions
    for k, v in data.azurerm_kubernetes_service_versions.k8s_version_prefixes : k => v.latest_version
  }
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
    name                 = var.node_pools["core"][0].name
    vm_size              = var.node_pools["core"][0].vm_size
    os_disk_size_gb      = var.node_pools["core"][0].os_disk_size_gb
    kubelet_disk_type    = var.node_pools["core"][0].kubelet_disk_type
    auto_scaling_enabled = true
    min_count            = var.node_pools["core"][0].min
    max_count            = var.node_pools["core"][0].max

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

  name                 = each.value.name
  vm_size              = each.value.vm_size
  os_disk_size_gb      = each.value.os_disk_size_gb
  kubelet_disk_type    = each.value.kubelet_disk_type
  auto_scaling_enabled = true
  min_count            = each.value.min
  max_count            = each.value.max

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

  name                 = each.value.name
  vm_size              = each.value.vm_size
  os_disk_size_gb      = each.value.os_disk_size_gb
  kubelet_disk_type    = each.value.kubelet_disk_type
  auto_scaling_enabled = true
  min_count            = each.value.min
  max_count            = each.value.max

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

output "kubeconfig" {
  value     = azurerm_kubernetes_cluster.jupyterhub.kube_config_raw
  sensitive = true
}
