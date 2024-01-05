tenant_id                      = "78aac226-2f03-4b4d-9037-b46d56c55210"
subscription_id                = "ead3521a-d994-4a44-a68d-b16e35642d5b"
resourcegroup_name             = "2i2c-utoronto-cluster"
global_container_registry_name = "2i2cutorontohubregistry"
global_storage_account_name    = "2i2cutorontohubstorage"
location                       = "canadacentral"

storage_size = 8192
ssh_pub_key  = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDQJ4h39UYNi1wybxAH+jCFkNK2aqRcuhDkQSMx0Hak5xkbt3KnT3cOwAgUP1Vt/SjhltSTuxpOHxiAKCRnjwRk60SxKhUNzPHih2nkfYTmBBjmLfdepDPSke/E0VWvTDIEXz/L8vW8aI0QGPXnXyqzEDO9+U1buheBlxB0diFAD3vEp2SqBOw+z7UgrGxXPdP+2b3AV+X6sOtd6uSzpV8Qvdh+QAkd4r7h9JrkFvkrUzNFAGMjlTb0Lz7qAlo4ynjEwzVN2I1i7cVDKgsGz9ZG/8yZfXXx+INr9jYtYogNZ63ajKR/dfjNPovydhuz5zQvQyxpokJNsTqt1CiWEUNj georgiana@georgiana"

# FIXME: upgrade to 1.27.7, and then 1.28.3, based on the latest versions
#        available via: az aks get-versions --location westus2 -o table
#
kubernetes_version = "1.26.3"

# FIXME: upgrade core_node_vm_size to Standard_E4s_v5
core_node_vm_size = "Standard_E4s_v3"

notebook_nodes = {
  "default" : {
    # NOTE: min-max below was set to 0-86 retroactively to align with
    #       observed state without understanding on why 0-86 was picked.
    min : 0,
    max : 86,
    # FIXME: upgrade user nodes vm_size to Standard_E8s_v5
    vm_size : "Standard_E8s_v3",
  }
}
