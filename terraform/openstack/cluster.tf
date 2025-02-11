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

# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_cluster_v1
resource "openstack_containerinfra_cluster_v1" "cluster" {
  name                = "${var.prefix}-cluster"
  cluster_template_id = openstack_containerinfra_clustertemplate_v1.template.id
  # There has to be at least 1 master node
  master_count        = 1
  node_count          = 1
  floating_ip_enabled = false
  merge_labels        = true
}

# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_nodegroup_v1
resource "openstack_containerinfra_nodegroup_v1" "core" {
  name           = "core-${var.prefix}"
  cluster_id     = openstack_containerinfra_cluster_v1.cluster.id
  node_count     = 1
  min_node_count = 1
  max_node_count = var.core_node_max_count
  flavor_id      = var.core_node_machine_type
  image_id       = var.image
  role           = "core"
  merge_labels   = true
  labels = {
    "hub.jupyter.org/node-purpose" = "core",
    "k8s.dask.org/node-purpose"    = "core"
  }
}

# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_nodegroup_v1
resource "openstack_containerinfra_nodegroup_v1" "nb" {
  for_each = var.notebook_nodes
  name     = "nb-${var.prefix}-${each.key}"

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

resource "openstack_containerinfra_nodegroup_v1" "dask" {
  for_each = var.dask_nodes
  name     = "dask-${var.prefix}-${each.key}"

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
