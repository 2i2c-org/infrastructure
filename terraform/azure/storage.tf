resource "azurerm_storage_account" "homes" {
  name                     = var.global_storage_account_name
  resource_group_name      = azurerm_resource_group.jupyterhub.name
  location                 = azurerm_resource_group.jupyterhub.location
  account_tier             = "Standard"
  account_kind             = "StorageV2"
  account_replication_type = "LRS"
}

resource "azurerm_storage_share" "homes" {
  name                 = "homes"
  storage_account_name = azurerm_storage_account.homes.name
  quota                = 100
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

resource "kubernetes_persistent_volume" "homes" {
  metadata {
    name = "homes"
  }
  spec {
    capacity = {
      storage = "1Mi"
    }
    access_modes = ["ReadWriteMany"]

    # See https://linux.die.net/man/8/mount.cifs for available options
    mount_options = [
      "uid=1000",
      "forceuid",
      "gid=1000",
      "forcegid",
      "nobrl"
    ]
    persistent_volume_source {
      azure_file {
        secret_name      = kubernetes_secret.homes.metadata[0].name
        secret_namespace = kubernetes_namespace.homes.metadata[0].name
        share_name       = azurerm_storage_share.homes.name
      }
    }
  }
}
