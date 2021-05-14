variable "prefix" {
  type = string
}

variable "project_id" {
  type = string
  # This is in Toronto!
  default = "two-eye-two-see"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-b"
}

variable "regional_cluster" {
  type    = string
  default = "false"
}

variable "core_node_machine_type" {
  type    = string
  default = "e2-highcpu-4"
}

variable "core_node_max_count" {
  type    = number
  default = 5
}

variable "core_node_disk_size_gb" {
  type    = number
  default = 50
}

variable "user_node_machine_type" {
  type    = string
  default = "n1-standard-4"
}

variable "user_node_max_count" {
  type    = number
  default = 10
}

variable "dask_worker_machine_type" {
  type    = string
  default = "e2-highmem-2"
}
