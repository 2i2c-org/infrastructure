tenant_id                   = "d61ecb3b-38b1-42d5-82c4-efb2838b925c"
subscription_id             = "cde71e96-035f-4b76-84ba-23d40a61897d"
resourcegroup_name          = "2i2c-jupyterhub-prod"
global_storage_account_name = "2i2cjupyterhubstorage"
location                    = "canadacentral"
budget_alert_amount         = null
storage_size                = 512
ssh_pub_key                 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBBQ9Fgc9s/Or8ZyFWVDU+a2s2dFPkviuX4tEK9l4oDYsbFLhZ3bHFSPFvVwI0G3rnSFzahzPQyAO/xugJJcDSV0= sgibson-2i2c"

kubernetes_version = "1.30.3"

node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E2s_v5",
      os_disk_size_gb : 40,
      kubelet_disk_type : "OS",  # Temporary disk does not have enough space
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
