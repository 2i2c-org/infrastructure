variable "prefix" {
  type = string
}

variable "region" {
  type = string
  # This is in Toronto!
  default = "Canada Central"
}

variable "user_vm_size" {
  type = string
  # VM with 32G of RAM, 8 cores, and ssd base disk
  default = "Standard_E8s_v3"
}

variable "core_vm_size" {
  type = string
  # 8GB of RAM, 4 CPU cores, ssd base disk
  # UNFORTUNATELY changing this triggers a k8s cluster recreation
  # BOOOO
  default = "Standard_F4s_v2"
}

variable "nfs_vm_size" {
  type = string
  # 8GB of RAM, 4 CPU cores, ssd base disk
  default = "Standard_F4s_v2"
}

variable "ssh_pub_key" {
  type = string
}
