# IMPORTANT: Due to a restrictive network rule from storage.tf, we can't perform
#            "terraform plan" or "terraform apply" without a workaround.
#
#            One known workaround is to allow your public IP temporarily as
#            discussed in https://github.com/2i2c-org/infrastructure/issues/890#issuecomment-1879072422.
#            This workaround is problematic as that may temporarily allow access
#            to storage by other actors with the same IP.
#
# SETTING UP TO WORK WITH THIS FILE:
# ----------------------------------
#
# The Azure account for this cluster has MFA enabled. The username, password and
# TOTP token are stored in the 2i2c shared Bitwarden account. To authenticate the
# Azure CLI, run:
#
#     az login --tenant f1123d69-0c31-44db-ab9f-fa856d721d49
#
tenant_id                      = "f1123d69-0c31-44db-ab9f-fa856d721d49"
subscription_id                = "4ca0b08a-26e1-482f-bca6-f4eb0926124a"
resourcegroup_name             = "2i2c-pchub"
global_container_registry_name = "2i2cpchub"
global_storage_account_name    = "2i2cpchub"
location                       = "westeurope"

storage_size = 100
ssh_pub_key  = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDEswiqOZ3cdu+OaT1K3ay8brlnnoHIpDyKNfLGeRAFQ4ZP+1OD82CIwrUiU4GhmiKTyyN9DWuKKhbEjMIrAKnoybQZBk/x21sHLyrqit1wq/X+f7/SKqDTFQGFYO5cERl/MwMRIp5WHEcLXi6WnaRczCQxOW6J36V5/frynz2Qq/3XwhQnkW9401HYt9H4Ur6JTZC0G0hMVklIT+gGsIml6Qu2O8+iuA2saGn3SCmTs7WBxVsEQTFt1w6JoJi4ohi7RtlT9QDSx4J+cawBNqzAK+gkozj2lN5Yiq7gtPJMe8sdLqmg9vSPCuAMMZeP+DhEGbre7Y+MMplSJrqkeT61WeCl39ffqwievGFkdTxzCiqX9TKSR2SS98W6jpCYrSkA1ymzn+HUADfyszU7sn6/F9I2w8oUbuFfMKDD4XfgkdK7Jqew7YJ4CDK2f4D94MWAmFicVKsYXPautnk+d3JqXarUN7k8bF9On2N8xZln0Zsui/Pmj1jQsnm0KXZOb9k= yuvipanda@instantaneous-authenticity.local"

# List available versions via: az aks get-versions --location westus2 -o table
kubernetes_version = "1.29.4"

# Free, the default, is not available in westeurope
cluster_sku_tier = "Standard"

node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E2_v4",

      # core nodes doesn't need much disk space
      os_disk_size_gb : 40,

      # FIXME: Stop using persistent disks for the nodes, use the variable default
      #        "Temporary" instead by removing this line.
      #        Currently does not work, as Azure seems to be buggy
      kubelet_disk_type : "OS",

      min : 1,
      max : 10,
    },
  ],

  user : [
    {
      name : "user",
      vm_size : "Standard_E2_v4",
      os_disk_size_gb : 100,
      min : 0,
      max : 100,
    },
  ],

  dask : [
    {
      name : "worker",
      vm_size : "Standard_E16_v4",
      os_disk_size_gb : 100,
      min : 0,
      max : 100,
    },
  ],
}
