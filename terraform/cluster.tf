resource "google_container_cluster" "cluster" {
  # config_connector_config is in beta
  provider = google-beta

  name     = "${var.prefix}-cluster"
  location = var.zone
  project  = var.project_id

  initial_node_count       = 1
  remove_default_node_pool = true

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

  release_channel {
    # We upgrade clusters manually so we can manage downtime of
    # master *and* nodes. When a cluster is in a release channel,
    # upgrades (including disruptive node upgrades) happen automatically.
    # So we disable it.
    channel = "UNSPECIFIED"
  }

  network_policy {
    enabled = var.enable_network_policy
  }

  node_config {
    # DO NOT TOUCH THIS BLOCK, IT REPLACES ENTIRE CLUSTER LOL
    service_account = google_service_account.cluster_sa.email
  }
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
    # granted via the service account.
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_container_node_pool" "notebook" {
  name     = "nb-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location

  for_each = var.notebook_nodes

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
    workload_metadata_config {
      // Use node concealment - https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata
      // This exposes the cluster Google SA to the pods, so we can
      // access GCS appropriately.
      node_metadata = "SECURE"
    }
    labels = {
      # Notebook pods and dask schedulers can exist here
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }

    taint = [{
      key    = "hub.jupyter.org_dedicated"
      value  = "user"
      effect = "NO_SCHEDULE"
    }]
    machine_type = each.value.machine_type

    # Our service account gets all OAuth scopes so it can access
    # all APIs, but only fine grained permissions + roles are
    # granted via the service account.
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_container_node_pool" "dask_worker" {
  name     = "dask-${each.key}"
  cluster  = google_container_cluster.cluster.name
  project  = google_container_cluster.cluster.project
  location = google_container_cluster.cluster.location

  # Default to same config as notebook nodepools config
  for_each = var.dask_nodes == {} ? var.dask_nodes : var.notebook_nodes

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
    # SSD Disks for dask workers make image pulls much faster
    # Since we might have many dask workers spinning up at the
    # same time, the extra cost of using this is probably worth it.
    disk_type = "pd-ssd"

    workload_metadata_config {
      // Use node concealment - https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata
      // This exposes the cluster Google SA to the pods, so we can
      // access GCS appropriately.
      node_metadata = "SECURE"
    }
    labels = {
      "k8s.dask.org/node-purpose" = "worker",
    }

    taint = [{
      key    = "k8s.dask.org_dedicated"
      value  = "worker"
      effect = "NO_SCHEDULE"
    }]
    machine_type = each.value.machine_type

    # Our service account gets all OAuth scopes so it can access
    # all APIs, but only fine grained permissions + roles are
    # granted via the service account.
    service_account = google_service_account.cluster_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

