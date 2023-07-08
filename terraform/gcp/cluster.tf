# This data resource and output provides information on the latest available k8s
# versions in GCP's regular release channel. This can be used when specifying
# versions to upgrade to via the k8s_versions variable.
#
# To get get the output of relevance, run:
#
#   terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
#   terraform output regular_channel_latest_k8s_versions
#
# data ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/container_engine_versions
data "google_container_engine_versions" "k8s_version_prefixes" {
  project  = var.project_id
  location = var.zone

  for_each       = var.k8s_version_prefixes
  version_prefix = each.value
}
output "regular_channel_latest_k8s_versions" {
  value = {
    for k, v in data.google_container_engine_versions.k8s_version_prefixes : k => v.release_channel_latest_version["REGULAR"]
  }
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_service_account
resource "google_service_account" "cluster_sa" {
  account_id   = "${var.prefix}-cluster-sa"
  display_name = "Service account used by nodes of cluster ${var.prefix}"
  project      = var.project_id
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam#google_project_iam_member
resource "google_project_iam_member" "cluster_sa_roles" {
  # https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster
  # has information on why the cluster SA needs these rights
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/artifactregistry.reader"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/google_container_cluster
resource "google_container_cluster" "cluster" {
  # Setting cluster autoscaling profile is in google-beta
  provider = google-beta

  name               = "${var.prefix}-cluster"
  location           = var.regional_cluster ? var.region : var.zone
  node_locations     = var.regional_cluster ? [var.zone] : null
  project            = var.project_id
  min_master_version = var.k8s_versions.min_master_version

  initial_node_count       = 1
  remove_default_node_pool = true
  lifecycle {
    # Any change to the default node_config forces cluster recreation,
    # and sometimes terraform seems to mess up and think we have changed
    # something here when we have not. So we explicitly ignore all changes
    # to node_config - we remove any nodepool it might create with
    # remove_default_node_pool = true.
    ignore_changes = [
      node_config
    ]

    # An additional safeguard against accidentally deleting the cluster.
    # The databases for the hubs are held in PVCs managed by the cluster,
    # so cluster deletion will cause data loss!
    prevent_destroy = true
  }

  // For private clusters, pass the name of the network and subnetwork created
  // by the VPC
  network    = var.enable_private_cluster ? data.google_compute_network.default_network.name : null
  subnetwork = var.enable_private_cluster ? data.google_compute_subnetwork.default_subnetwork.name : null

  // Dynamically provision the private cluster config when deploying a
  // private cluster
  dynamic "private_cluster_config" {
    for_each = var.enable_private_cluster ? [1] : []

    content {
      // Decide if this CIDR block is sensible or not
      master_ipv4_cidr_block  = "172.16.0.0/28"
      enable_private_nodes    = true
      enable_private_endpoint = false
    }
  }

  // Dynamically provision the IP allocation policy when deploying a
  // private cluster. This allows for IP aliasing and makes the cluster
  // VPC-native
  dynamic "ip_allocation_policy" {
    for_each = var.enable_private_cluster ? [1] : []
    content {}
  }

  addons_config {
    http_load_balancing {
      // FIXME: This used to not work well with websockets, and
      // cost extra money as well. Let's validate if this is still
      // true?
      disabled = true
    }
    horizontal_pod_autoscaling {
      // This isn't used anywhere, so let's turn this off
      disabled = true
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    # We upgrade clusters manually so we can manage downtime of
    # master *and* nodes. When a cluster is in a release channel,
    # upgrades (including disruptive node upgrades) happen automatically.
    # So we disable it.
    channel = "UNSPECIFIED"
  }

  cluster_autoscaling {
    # This disables node autoprovisioning, not cluster autoscaling!
    enabled = var.enable_node_autoprovisioning
    # Use a scheduler + autoscaling profile optimized for batch workloads like ours
    # https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler#autoscaling_profiles
    autoscaling_profile = "OPTIMIZE_UTILIZATION"

    // When node auto-provisioning is enabled, set the min and max amount of
    // CPU and memory to allocate
    dynamic "resource_limits" {
      for_each = var.enable_node_autoprovisioning ? [1] : []

      content {
        resource_type = "memory"
        minimum       = var.min_memory
        maximum       = var.max_memory
      }
    }

    dynamic "resource_limits" {
      for_each = var.enable_node_autoprovisioning ? [1] : []

      content {
        resource_type = "cpu"
        minimum       = var.min_cpu
        maximum       = var.max_cpu
      }
    }
  }

  network_policy {
    enabled = var.enable_network_policy
  }

  node_config {
    # DO NOT TOUCH THIS BLOCK, IT REPLACES ENTIRE CLUSTER LOL
    service_account = google_service_account.cluster_sa.email
  }

  monitoring_config {
    managed_prometheus {
      # We do not use GCP managed Prometheus, but our own installation.
      # So we do not install the managed prometheus collector on every node,
      # saving some resources on each node.
      enabled = false
    }
  }

  // Set these values explicitly so they don't "change outside terraform"
  resource_labels = {}
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/container_node_pool
resource "google_container_node_pool" "core" {
  name     = "core-pool"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location
  version  = var.k8s_versions.core_nodes_version


  initial_node_count = 1
  autoscaling {
    min_node_count = 1
    max_node_count = var.core_node_max_count
  }

  lifecycle {
    # Even though it says 'initial'_node_count, it actually represents 'current' node count!
    # So if the current number of nodes is different than the initial number (due to autoscaling),
    # terraform will destroy & recreate the nodepool unnecessarily! Hence, we ignore any changes to
    # this number after initial creation.
    # See https://github.com/hashicorp/terraform-provider-google/issues/6901#issuecomment-667369691 for
    # more details.
    ignore_changes = [
      initial_node_count
    ]
  }

  management {
    auto_repair = true
    # Auto upgrade will drain and setup nodes without us knowing,
    # and this can cause outages when it hits the proxy nodes.
    auto_upgrade = false
  }


  node_config {
    labels = {
      "hub.jupyter.org/node-purpose" = "core",
      "k8s.dask.org/node-purpose"    = "core"
    }
    machine_type = var.core_node_machine_type
    disk_size_gb = 30

    # Our service account gets all OAuth scopes so it can access
    # all APIs, but only fine grained permissions + roles are
    # granted via the service account. This follows Google's
    # recommendation at https://cloud.google.com/compute/docs/access/service-accounts#associating_a_service_account_to_an_instance
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    // Set these values explicitly so they don't "change outside terraform"
    tags = []
  }
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/container_node_pool
resource "google_container_node_pool" "notebook" {
  for_each = var.notebook_nodes

  name     = "nb-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location
  version  = var.k8s_versions.notebook_nodes_version

  # terraform treats null same as unset, so we only set the node_locations
  # here if it is explicitly overriden. If not, it will just inherit whatever
  # is set for the cluster.
  node_locations = length(each.value.zones) == 0 ? null : each.value.zones

  initial_node_count = each.value.min
  autoscaling {
    min_node_count = each.value.min
    max_node_count = each.value.max
  }

  lifecycle {
    # Even though it says 'initial'_node_count, it actually represents 'current' node count!
    # So if the current number of nodes is different than the initial number (due to autoscaling),
    # terraform will destroy & recreate the nodepool unnecessarily! Hence, we ignore any changes to
    # this number after initial creation.
    # See https://github.com/hashicorp/terraform-provider-google/issues/6901#issuecomment-667369691 for
    # more details.
    ignore_changes = [
      initial_node_count
    ]
  }

  management {
    auto_repair  = true
    auto_upgrade = false
  }


  node_config {

    # Balanced disks are much faster than standard disks, and much cheaper
    # than SSD disks. It contributes heavily to how fast new nodes spin up,
    # as images being pulled takes up a lot of new node spin up time.
    # Faster disks provide faster image pulls!
    disk_type = "pd-balanced"

    dynamic "guest_accelerator" {
      for_each = each.value.gpu.enabled ? [1] : []

      content {
        type  = each.value.gpu.type
        count = each.value.gpu.count
      }

    }

    workload_metadata_config {
      # Config Connector requires workload identity to be enabled (via GKE_METADATA_SERVER).
      # If config connector is not necessary, we use simple metadata concealment
      # (https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata)
      # to expose the node CA to users safely.
      # FIXME: This should be a bit more fine-grained - it should be possible to disable
      # config connector and completely hide all node metadata from user pods
      mode = "GKE_METADATA"
    }
    labels = merge({
      # Notebook pods and dask schedulers can exist here
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }, each.value.labels)

    taint = concat([{
      key    = "hub.jupyter.org_dedicated"
      value  = "user"
      effect = "NO_SCHEDULE"
      }],
      # Add extra taint explicitly if GPU is enabled, so non-GPU pods aren't scheduled here
      # Terraform implicitly adds this taint anyway, and tries to recreate the nodepool if we re-apply
      each.value.gpu.enabled ? [{
        effect = "NO_SCHEDULE"
        key    = "nvidia.com/gpu"
        value  = "present"
      }] : [],
      each.value.taints
    )
    machine_type = each.value.machine_type

    # Our service account gets all OAuth scopes so it can access
    # all APIs, but only fine grained permissions + roles are
    # granted via the service account. This follows Google's
    # recommendation at https://cloud.google.com/compute/docs/access/service-accounts#associating_a_service_account_to_an_instance
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    resource_labels = each.value.resource_labels

    // Set these values explicitly so they don't "change outside terraform"
    tags = []
  }
}

# resource ref: https://registry.terraform.io/providers/hashicorp/google-beta/latest/docs/resources/container_node_pool
resource "google_container_node_pool" "dask_worker" {
  name     = "dask-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location
  version  = var.k8s_versions.dask_nodes_version

  # terraform treats null same as unset, so we only set the node_locations
  # here if it is explicitly overriden. If not, it will just inherit whatever
  # is set for the cluster.
  node_locations = length(each.value.zones) == 0 ? null : each.value.zones

  # Default to same config as notebook nodepools config
  for_each = var.dask_nodes

  # WARNING: Do not change this value, it will cause the nodepool
  # to be destroyed & re-created. If you want to increase number of
  # nodes in a node pool, set the min count to that number and then
  # scale the pool manually.
  initial_node_count = 0
  autoscaling {
    min_node_count = each.value.min
    max_node_count = each.value.max
  }

  management {
    auto_repair  = true
    auto_upgrade = false
  }

  node_config {

    preemptible = each.value.preemptible

    # Balanced disks are much faster than standard disks, and much cheaper
    # than SSD disks. It contributes heavily to how fast new nodes spin up,
    # as images being pulled takes up a lot of new node spin up time.
    # Faster disks provide faster image pulls!
    disk_type = "pd-balanced"

    workload_metadata_config {
      # Config Connector requires workload identity to be enabled (via GKE_METADATA_SERVER).
      # If config connector is not necessary, we use simple metadata concealment
      # (https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata)
      # to expose the node CA to users safely.
      # FIXME: This should be a bit more fine-grained - it should be possible to disable
      # config connector and completely hide all node metadata from user pods
      mode = "GKE_METADATA"
    }
    labels = merge({
      "k8s.dask.org/node-purpose" = "worker",
    }, each.value.labels)

    taint = concat([{
      key    = "k8s.dask.org_dedicated"
      value  = "worker"
      effect = "NO_SCHEDULE"
      }],
      each.value.taints
    )

    machine_type = each.value.machine_type

    # Our service account gets all OAuth scopes so it can access
    # all APIs, but only fine grained permissions + roles are
    # granted via the service account. This follows Google's
    # recommendation at https://cloud.google.com/compute/docs/access/service-accounts#associating_a_service_account_to_an_instance
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    resource_labels = each.value.resource_labels

    // Set these values explicitly so they don't "change outside terraform"
    tags = []
  }
}
