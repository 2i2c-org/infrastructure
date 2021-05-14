terraform {
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

module "service_accounts" {
  source        = "terraform-google-modules/service-accounts/google"
  version       = "~> 2.0"
  project_id    = var.project_id
  prefix        = var.prefix
  generate_keys = true
  names         = ["cd-sa"]
  project_roles = [
    "${var.project_id}=>roles/container.admin",
    "${var.project_id}=>roles/artifactregistry.writer",
    # FIXME: This is way too much perms just to ssh into a node
    "${var.project_id}=>roles/compute.instanceAdmin.v1"
  ]
}

output "ci_deployer_key" {
  value     = module.service_accounts.keys["cd-sa"]
  sensitive = true
}

resource "google_artifact_registry_repository" "container_repository" {
  provider = google-beta

  location      = var.region
  repository_id = "low-touch-hubs"
  format        = "DOCKER"
  project       = var.project_id
}

// Give the GKE service account access to our artifact registry docker repo
resource "google_project_iam_member" "project" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${module.gke.service_account}"
}


module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  project_id                 = var.project_id
  name                       = "${var.prefix}-cluster"
  regional                   = var.regional_cluster
  region                     = var.region
  zones                      = [var.zone]
  network                    = "default"
  subnetwork                 = "default"
  ip_range_pods              = ""
  ip_range_services          = ""
  http_load_balancing        = false
  horizontal_pod_autoscaling = false
  network_policy             = true
  # We explicitly set up a core pool, so don't need the default
  remove_default_node_pool = true
  kubernetes_version       = "1.19.9-gke.1400"


  node_pools = [
    {
      name               = "core-pool"
      machine_type       = var.core_node_machine_type
      min_count          = 1
      max_count          = var.core_node_max_count
      local_ssd_count    = 0
      disk_size_gb       = var.core_node_disk_size_gb
      disk_type          = "pd-standard"
      image_type         = "COS"
      auto_repair        = true
      auto_upgrade       = false
      preemptible        = false
      initial_node_count = 1
      # Let's pin this so we don't upgrade each time terraform runs
      version = "1.19.9-gke.1400"
    },
    {
      name               = "user-pool"
      machine_type       = var.user_node_machine_type
      min_count          = 0
      max_count          = var.user_node_max_count
      local_ssd_count    = 0
      disk_size_gb       = 100
      disk_type          = "pd-ssd"
      image_type         = "COS"
      auto_repair        = true
      auto_upgrade       = false
      preemptible        = false
      initial_node_count = 0
      # Let's pin this so we don't upgrade each time terraform runs
      version = "1.19.9-gke.1400"
    },
    {
      name            = "dask-worker-pool"
      machine_type    = var.dask_worker_machine_type
      min_count       = 0
      max_count       = 10
      local_ssd_count = 0
      disk_size_gb    = 100
      # Fast startup is important here, so we get fast SSD disks
      # This pulls in user images much faster
      disk_type          = "pd-ssd"
      image_type         = "COS"
      auto_repair        = true
      auto_upgrade       = false
      preemptible        = true
      initial_node_count = 0
      # Let's pin this so we don't upgrade each time terraform runs
      version = "1.19.9-gke.1400"
    },
  ]

  node_pools_oauth_scopes = {
    all = [
      # FIXME: Is this the minimal?
      #
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  node_pools_labels = {
    all = {}

    core-pool = {
      default-node-pool              = true
      "hub.jupyter.org/pool-name"    = "core-pool",
      "hub.jupyter.org/node-purpose" = "core",
      "k8s.dask.org/node-purpose"    = "core"
    }
    user-pool = {
      "hub.jupyter.org/pool-name"    = "user-pool"
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler"
    }
    dask-worker-pool = {
      "hub.jupyter.org/pool-name" = "dask-worker-pool"
      "k8s.dask.org/node-purpose" = "worker"
    }
  }

  node_pools_taints = {
    all = []

    user-pool = [{
      key    = "hub.jupyter.org_dedicated"
      value  = "user"
      effect = "NO_SCHEDULE"
    }]
    dask-worker-pool = [{
      key    = "k8s.dask.org_dedicated"
      value  = "worker"
      effect = "NO_SCHEDULE"
    }]
  }
}
