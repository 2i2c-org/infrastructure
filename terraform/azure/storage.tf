resource "azurerm_storage_account" "homes" {
  name                     = var.global_storage_account_name
  resource_group_name      = azurerm_resource_group.jupyterhub.name
  location                 = azurerm_resource_group.jupyterhub.location
  account_tier             = var.storage_protocol != "NFS" ? "Standard" : "Premium"
  account_kind             = var.storage_protocol != "NFS" ? "StorageV2" : "FileStorage"
  account_replication_type = "LRS"
}

resource "azurerm_storage_share" "homes" {
  name                 = "homes"
  storage_account_name = azurerm_storage_account.homes.name
  quota                = 100
  enabled_protocol     = var.storage_protocol
}

resource "kubernetes_namespace" "homes" {
  metadata {
    name = "azure-file"
  }
}

resource "kubernetes_secret" "homes" {
  metadata {
    name      = "access-credentials"
    namespace = kubernetes_namespace.homes.metadata[0].name
  }

  data = {
    azurestorageaccountname = azurerm_storage_account.homes.name
    azurestorageaccountkey  = azurerm_storage_account.homes.primary_access_key
  }
}
