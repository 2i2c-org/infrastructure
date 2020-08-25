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
  # 16GB of RAM, 2 cores, ssd base disk
  default = "Standard_E2s_v3"
}

variable "ssh_pub_key" {
  type = string
}
