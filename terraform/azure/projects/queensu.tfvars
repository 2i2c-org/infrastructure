tenant_id                   = "d61ecb3b-38b1-42d5-82c4-efb2838b925c"
subscription_id             = "cde71e96-035f-4b76-84ba-23d40a61897d"
resourcegroup_name          = "2i2c-jupyterhub-prod"
global_storage_account_name = "2i2cjupyterhubstorage"
location                    = "canadacentral"
budget_alert_amount         = null
storage_size                = 512
ssh_pub_key                 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBInYkhcbNZoDtGFcY6zWdcqO3G9VlVxTc8ECW7/VpAhbetuUpe7T9eo0oGx+Y3ZBrlLZMyd1RpQiUzVKWEoDPB0= sgibson@2i2c.org"

kubernetes_version = "1.30.3"

node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E2s_v5",
      os_disk_size_gb : 40,
      min : 1,
      max : 10,
    },
  ],
  user : [
    {
      name : "usere8sv5",
      vm_size : "Standard_E8s_v5",
      os_disk_size_gb : 200,
      min : 0,
      max : 100,
    },
  ],
  dask : [],
}
