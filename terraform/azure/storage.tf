resource "azurerm_storage_account" "homes" {
  name                     = var.global_storage_account_name
  resource_group_name      = azurerm_resource_group.jupyterhub.name
  location                 = azurerm_resource_group.jupyterhub.location
  account_tier             = "Premium"
  account_kind             = "FileStorage"
  account_replication_type = "LRS"

  # Disable 'secure link' because we only want to use NFS
  # see https://docs.microsoft.com/en-us/azure/storage/files/storage-files-how-to-mount-nfs-shares#disable-secure-transfer
  enable_https_traffic_only = false

  network_rules {
    # Allow NFS access only from our nodes, deny access from all other networks
    #
    # Use of terraform plan or apply can run into issues due to this, but they
    # can be handled by temporarily adding your public IP to a firewall
    # exception like described in
    # https://github.com/2i2c-org/infrastructure/issues/890#issuecomment-1879072422.
    #
    default_action = "Deny"
    virtual_network_subnet_ids = [
      azurerm_subnet.node_subnet.id
    ]
  }
}

resource "azurerm_storage_share" "homes" {
  name                 = "homes"
  storage_account_name = azurerm_storage_account.homes.name
  quota                = var.storage_size
  enabled_protocol     = "NFS"
  lifecycle {
    # Additional safeguard against deleting the share
    # as this causes irreversible data loss!
    prevent_destroy = true
  }
}

output "azure_fileshare_url" {
  value = azurerm_storage_share.homes.url
}

resource "azurerm_recovery_services_vault" "homedir_recovery_vault" {
  name                = "homedir-recovery-vault"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  sku                 = "Standard"
}

resource "azurerm_backup_policy_file_share" "backup_policy" {
  name                = "homedir-recovery-vault-policy"
  resource_group_name = azurerm_resource_group.jupyterhub.name
  recovery_vault_name = azurerm_recovery_services_vault.homedir_recovery_vault.name

  timezone = "UTC-07:00"

  backup {
    frequency = "Daily"
    time      = "22:00"
  }

  retention_daily {
    count = 5
  }
}
