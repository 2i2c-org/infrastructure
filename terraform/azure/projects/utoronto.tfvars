# IMPORTANT: Due to a restrictive network rule from storage.tf, we can't perform
#            "terraform plan" or "terraform apply" without a workaround.
#
#            One known workaround is to allow your public IP temporarily as
#            discussed in https://github.com/2i2c-org/infrastructure/issues/890#issuecomment-1879072422.
#            This workaround is problematic as that may temporarily allow access
#            to storage by other actors with the same IP.
#
tenant_id                      = "78aac226-2f03-4b4d-9037-b46d56c55210"
subscription_id                = "ead3521a-d994-4a44-a68d-b16e35642d5b"
resourcegroup_name             = "2i2c-utoronto-cluster"
global_container_registry_name = "2i2cutorontohubregistry"
global_storage_account_name    = "2i2cutorontohubstorage"
location                       = "canadacentral"

storage_size = 10240
ssh_pub_key  = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQJ4h39UYNi1wybxAH+jCFkNK2aqRcuhDkQSMx0Hak5xkbt3KnT3cOwAgUP1Vt/SjhltSTuxpOHxiAKCRnjwRk60SxKhUNzPHih2nkfYTmBBjmLfdepDPSke/E0VWvTDIEXz/L8vW8aI0QGPXnXyqzEDO9+U1buheBlxB0diFAD3vEp2SqBOw+z7UgrGxXPdP+2b3AV+X6sOtd6uSzpV8Qvdh+QAkd4r7h9JrkFvkrUzNFAGMjlTb0Lz7qAlo4ynjEwzVN2I1i7cVDKgsGz9ZG/8yZfXXx+INr9jYtYogNZ63ajKR/dfjNPovydhuz5zQvQyxpokJNsTqt1CiWEUNj georgiana@georgiana"

# List available versions via: az aks get-versions --location westus2 -o table
kubernetes_version = "1.28.3"

node_pools = {
  core : [
    {
      name : "core",

      # FIXME: Transition to "Standard_E2s_v5" nodes as they are large enough to
      #        for the biggest workload (prometheus-server) and can handle high
      #        availability requirements better.
      #
      #        We are currently forced to handle three calico-typha pods that
      #        can't schedule on the same node, see https://github.com/2i2c-org/infrastructure/issues/3592#issuecomment-1883269632.
      #
      vm_size : "Standard_E4s_v3",

      # core nodes doesn't need much disk space
      os_disk_size_gb : 40,

      # FIXME: Stop using persistent disks for the nodes, use the variable default
      #        "Temporary" instead by removing this line.
      kubelet_disk_type : "OS",

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
