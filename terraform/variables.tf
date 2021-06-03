variable "prefix" {
  type        = string
  description = "Prefix used for all objects, to prevent collisions in the project"
}

variable "project_id" {
  type        = string
  description = "ID of the GCP project resources should be created in"
}

variable "notebook_nodes" {
  type        = map(map(string))
  description = "Notebook node pools to create"
  default     = {}
}

variable "dask_nodes" {
  type        = map(map(string))
  description = "Dask node pools to create. Defaults to notebook_nodes"
  default     = {}
}

variable "config_connector_enabled" {
  type        = bool
  default     = false
  description = "Enable config connector to manage GCP resources as kubernetes objects"
}

variable "cluster_sa_roles" {
  type = set(string)
  default = [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/artifactregistry.reader"
  ]
  description = "List of roles for the service account the nodes in the cluster run as"
}

variable "cd_sa_roles" {
  type = set(string)
  default = [
    "roles/container.admin",
    "roles/artifactregistry.writer"
  ]
  description = "List of roles for the service account used for continuous deployment"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region the resources should be created in"

}

variable "zone" {
  type        = string
  default     = "us-central1-b"
  description = "GCP Zone the nodes of the cluster should be created in"
}

variable "regional_cluster" {
  type        = string
  default     = "false"
  description = "Set to 'true' for a HA regional master"
}

variable "core_node_machine_type" {
  type        = string
  default     = "g1-small"
  description = "Machine type for core nodes"
}

variable "core_node_max_count" {
  type        = number
  default     = 5
  description = "Maximum number of core nodes allowed"
}


variable "enable_network_policy" {
  type        = bool
  default     = true
  description = "Enable kubernetes network policy for access to fine-grained firewall rules"
}

variable "user_buckets" {
  type        = set(any)
  default     = []
  description = "Buckets to create for the project, they will be prefixed with {var.prefix}-"
}
