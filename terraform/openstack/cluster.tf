# This terraform creates some resources that are subject to compromises because
# of some limitations of the magnum driver.
# 1. Concurrent nodegroups creation requests fired by terraform fail because of
#    a race condition in the magnum driver. This means that `terraform apply`
#    must be ran with `--parallelism=1` to avoid this issue.
#    # https://bugs.launchpad.net/magnum/+bug/2097946
# 2. The role and labels of the nodegroups don't get propagated to the actual
#    nodes. This means that we cannot add the node-purpose labels that z2jh
#    expects and instead we need to rely on the only label that gets added by
#    the magnum driver and can identify the node, capi.stackhpc.com/node-group.
#    This in turn, forces us to only offer one machine type per notebook/dask/gpu
#    for the users.
#    https://github.com/azimuth-cloud/capi-helm-charts/issues/84
# 3. The node count and min node count cannot be set to 0 and each nodegroup has
#    to have at least 1 node.
#    https://bugs.launchpad.net/magnum/+bug/2098002
# 4. A default-worker is created apart from the default-controlplane nodegroup
#    is created and we cannot delete it due to the same issue as in 2.

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
  name           = "core"
  cluster_id     = openstack_containerinfra_cluster_v1.cluster.id
  node_count     = 1
  min_node_count = 1
  max_node_count = var.core_node_max_count
  flavor_id      = var.core_node_machine_type
  image_id       = var.image
  merge_labels   = true

  # Due to a bug in the capi magnum driver, the role and labels don't get
  # propagated to the actual nodes. So the following config has no effect.
  role = "core"
  labels = {
    "hub.jupyter.org/node-purpose" = "core",
    "k8s.dask.org/node-purpose"    = "core"
  }
}

# https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/containerinfra_nodegroup_v1
resource "openstack_containerinfra_nodegroup_v1" "nb" {
  for_each = var.notebook_nodes
  name     = "user-${each.key}"

  cluster_id = openstack_containerinfra_cluster_v1.cluster.id
  flavor_id  = each.value.machine_type
  image_id   = var.image
  # Due to a bug in the capi magnum driver the node count and min node count
  # cannot be set to 0 and each nodegroup has to have at least 1 node
  node_count     = 1
  min_node_count = each.value.min
  max_node_count = each.value.max
  merge_labels   = true
  # Due to a bug in the capi magnum driver, the role and labels don't get
  # propagated to the actual nodes. So the following config has no effect.
  labels = each.value.labels
  role   = each.value.role
}

resource "openstack_containerinfra_nodegroup_v1" "dask" {
  for_each = var.dask_nodes
  name     = "dask-${var.prefix}-${each.key}"

  cluster_id = openstack_containerinfra_cluster_v1.cluster.id
  flavor_id  = each.value.machine_type
  image_id   = var.image
  # Due to a bug in the capi magnum driver the node count and min node count
  # cannot be set to 0 and each nodegroup has to have at least 1 node
  node_count     = 1
  min_node_count = each.value.min
  max_node_count = each.value.max
  merge_labels   = true
  # Due to a bug in the capi magnum driver, the role and labels don't get
  # propagated to the actual nodes. So the following config has no effect.
  role   = each.value.role
  labels = each.value.labels
}
