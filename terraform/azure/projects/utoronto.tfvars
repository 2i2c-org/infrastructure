tenant_id                      = "78aac226-2f03-4b4d-9037-b46d56c55210"
subscription_id                = "ead3521a-d994-4a44-a68d-b16e35642d5b"
resourcegroup_name             = "2i2c-utoronto-cluster"
global_container_registry_name = "2i2cutorontohubregistry"
global_storage_account_name    = "2i2cutorontohubstorage"
location                       = "canadacentral"

storage_size = 8192
ssh_pub_key  = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQJ4h39UYNi1wybxAH+jCFkNK2aqRcuhDkQSMx0Hak5xkbt3KnT3cOwAgUP1Vt/SjhltSTuxpOHxiAKCRnjwRk60SxKhUNzPHih2nkfYTmBBjmLfdepDPSke/E0VWvTDIEXz/L8vW8aI0QGPXnXyqzEDO9+U1buheBlxB0diFAD3vEp2SqBOw+z7UgrGxXPdP+2b3AV+X6sOtd6uSzpV8Qvdh+QAkd4r7h9JrkFvkrUzNFAGMjlTb0Lz7qAlo4ynjEwzVN2I1i7cVDKgsGz9ZG/8yZfXXx+INr9jYtYogNZ63ajKR/dfjNPovydhuz5zQvQyxpokJNsTqt1CiWEUNj georgiana@georgiana"

# List available versions via: az aks get-versions --location westus2 -o table
kubernetes_version = "1.28.3"

core_node_pool = {
  name : "core",
  kubernetes_version : "1.28.3",

  # FIXME: transition to "Standard_E2s_v5" nodes as they are large enough and
  #        can more cheaply handle being forced to have 2-3 replicas for silly
  #        reasons like three calico-typha pods. See
  #        https://github.com/2i2c-org/infrastructure/issues/3592#issuecomment-1883269632.
  #
  #        Transitioning to E2s_v5 would require reducing the requested memory
  #        by prometheus-server though, but that should be okay since
  #        prometheus has reduced its memory profile significant enough recently.
  #
  vm_size : "Standard_E4s_v3",

  # FIXME: stop using persistent disks for the nodes, use the variable default
  #        "Temporary" instead
  kubelet_disk_type : "OS",

  # FIXME: use a larger os_disk_size_gb than 40, like the default of 100, to
  #        avoid running low when few replicas are used
  os_disk_size_gb : 40,

  # FIXME: its nice to use autoscaling, but we end up with three replicas due to
  #        https://github.com/2i2c-org/infrastructure/issues/3592#issuecomment-1883269632
  #        and its a waste at least using Standard_E4s_v3 machines.
  enable_auto_scaling : false,
  node_count : 2,
}

user_node_pools = {
  "default" : {
    name : "nbdefault",
    # NOTE: min-max below was set to 0-86 retroactively to align with
    #       observed state without understanding on why 0-86 was picked.
    min : 0,
    max : 86,
    # FIXME: upgrade user nodes vm_size to Standard_E8s_v5
    vm_size : "Standard_E8s_v3",
    # FIXME: remove this label
    labels : {
      "hub.jupyter.org/node-size" = "Standard_E8s_v3",
    },
    kubernetes_version : "1.26.3",
    # FIXME: stop using persistent disks for the nodes, use Temporary instead
    kubelet_disk_type : "OS",
  },
  "usere8sv5" : {
    min : 0,
    max : 100,
    vm_size : "Standard_E8s_v5",
  }
}
