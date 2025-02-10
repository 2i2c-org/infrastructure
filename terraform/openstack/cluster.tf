variable "prefix" {
  type        = string
  description = <<-EOT
  Prefix for all objects created by terraform.

  Primary identifier to 'group' together resources created by
  this terraform module. Prevents clashes with other resources
  in the cloud project / account.

  Should not be changed after first terraform apply - doing so
  will recreate all resources.

  Should not end with a '-', that is automatically added.
  EOT
}
# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_clustertemplate_v1#master_flavor-1
variable "master_flavor" {
  type        = string
  default     = "m3.small"
  description = "Machine type for the master nodes"
}

# Picked latest ubuntu image from `openstack image list`
variable "image" {
  type    = string
  default = "ubuntu-jammy-kube-v1.31.0-240828-1652"
}

# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_clustertemplate_v1
resource "openstack_containerinfra_clustertemplate_v1" "template" {
  name                = "${var.image}-template"
  coe                 = "kubernetes"
  server_type         = "vm"
  tls_disabled        = false
  image               = var.image
  external_network_id = "public"
  # disable load balancer for master nodes since we're having only one master node
  master_lb_enabled   = false
  floating_ip_enabled = false
  network_driver      = "calico"
  flavor              = var.master_flavor
  master_flavor       = var.master_flavor
  labels = {
    monitoring_enabled               = "false" # these will handled by the support chart
    prometheus_monitoring            = "false" # these will handled by the support chart
    influx_grafana_dashboard_enabled = "false" # these will handled by the support chart
    kube_dashboard_enabled           = "false"
    auto_scaling_enabled             = "true"
    min_node_count                   = 1
  }
}

output "template" {
  value = openstack_containerinfra_clustertemplate_v1.template
}

resource "openstack_containerinfra_cluster_v1" "cluster" {
  name                = "${var.prefix}-cluster"
  cluster_template_id = openstack_containerinfra_clustertemplate_v1.template.id
  master_count        = 1
  floating_ip_enabled = false
  node_count          = 1
  merge_labels        = true
}

variable "nodegroups" {
  type = map(object({
    min : number,
    max : number,
    machine_type : string,
    role : string,
    labels : optional(map(string), {}),
  }))
  description = "Node pools to create"
  default = {
    "core" : {
      min : 1,
      max : 10,
      machine_type : "m3.small",
      role : "core",
      labels = {
        "hub.jupyter.org/node-purpose" = "core",
        "k8s.dask.org/node-purpose"    = "core"
      }
    },
    "nb" : {
      min : 1,
      max : 100,
      machine_type : "m3.small",
      role : "notebook",
      labels = {
        "hub.jupyter.org/node-purpose" = "user",
        "k8s.dask.org/node-purpose"    = "scheduler",
      }
    },
  }
}


# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_nodegroup_v1
resource "openstack_containerinfra_nodegroup_v1" "nodes" {
  for_each = var.nodegroups

  name           = "${var.prefix}-${each.key}"
  cluster_id     = openstack_containerinfra_cluster_v1.cluster.id
  flavor_id      = each.value.machine_type
  image_id       = var.image
  role           = each.value.role
  node_count     = 1
  min_node_count = each.value.min
  max_node_count = each.value.max
  merge_labels   = true
  labels         = each.value.labels
}

# # https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_nodegroup_v1
# resource "openstack_containerinfra_nodegroup_v1" "notebook-2" {
#   name           = "${var.prefix}-nb-2"
#   cluster_id     = openstack_containerinfra_cluster_v1.cluster.id
#   min_node_count = 1
#   node_count     = 1
#   # max_node_count = 5
#   flavor_id      = var.nb_machine_type
#   image_id       = var.image
#   role           = "nb"
#   merge_labels   = true
#   labels = {
#     "hub.jupyter.org/node-purpose" = "user",
#     "k8s.dask.org/node-purpose"    = "scheduler",
#   }
# }