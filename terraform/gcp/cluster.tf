resource "google_container_cluster" "cluster" {
  # config_connector_config is in beta
  provider = google-beta

  name     = "${var.prefix}-cluster"
  location = var.zone
  project  = var.project_id

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
    config_connector_config {
      enabled = var.config_connector_enabled
    }
  }

  dynamic "workload_identity_config" {
    # Setup workload identity only if we're using config connector, otherwise
    # just metadata concealment is used
    for_each = var.config_connector_enabled == "" ? [] : [1]
    content {
      workload_pool = "${var.project_id}.svc.id.goog"
    }
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

  // Set these values explicitly so they don't "change outside terraform"
  resource_labels = {}
}

resource "google_container_node_pool" "core" {
  name     = "core-pool"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location


  initial_node_count = 1
  autoscaling {
    min_node_count = 1
    max_node_count = var.core_node_max_count
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

resource "google_container_node_pool" "notebook" {
  name     = "nb-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location

  for_each = var.notebook_nodes

  # WARNING: Do not change this value, it will cause the nodepool
  # to be destroyed & re-created. If you want to increase number of
  # nodes in a node pool, set the min count to that number and then
  # scale the pool manually.
  initial_node_count = each.value.min
  autoscaling {
    min_node_count = each.value.min
    max_node_count = each.value.max
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

    workload_metadata_config {
      # Config Connector requires workload identity to be enabled (via GKE_METADATA_SERVER).
      # If config connector is not necessary, we use simple metadata concealment
      # (https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata)
      # to expose the node CA to users safely.
      # FIXME: This should be a bit more fine-grained - it should be possible to disable
      # config connector and completely hide all node metadata from user pods
      mode = var.config_connector_enabled ? "GKE_METADATA" : "MODE_UNSPECIFIED"
    }
    labels = merge({
      # Notebook pods and dask schedulers can exist here
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }, each.value.labels)

    taint = [{
      key    = "hub.jupyter.org_dedicated"
      value  = "user"
      effect = "NO_SCHEDULE"
    }]
    machine_type = each.value.machine_type

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

resource "google_container_node_pool" "dask_worker" {
  name     = "dask-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location

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

    preemptible = true

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
      mode = var.config_connector_enabled ? "GKE_METADATA" : "MODE_UNSPECIFIED"
    }
    labels = merge({
      "k8s.dask.org/node-purpose" = "worker",
    }, each.value.labels)

    taint = [{
      key    = "k8s.dask.org_dedicated"
      value  = "worker"
      effect = "NO_SCHEDULE"
    }]
    machine_type = each.value.machine_type

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
