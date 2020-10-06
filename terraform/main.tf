terraform {
  backend "gcs" {
    bucket  = "2i2c-terraform-state"
    prefix  = "terraform/state/low-touch-hubs"
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
      "${var.project_id}=>roles/artifactregistry.writer"
  ]
}

output "ci_deployer_key" {
  value = module.service_accounts.keys["cd-sa"]
}

resource "google_artifact_registry_repository" "container_repository" {
  provider = google-beta

  location = var.region
  repository_id = "low-touch-user-image"
  format = "DOCKER"
  project = var.project_id
}


module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  project_id                 = var.project_id
  name                       = "${var.prefix}-cluster"
  regional                   = "true" # Pay some money for higher resiliencey
  region                     = var.region
  zones                      = [var.zone]
  network                    = "default"
  subnetwork                 = "default"
  ip_range_pods              = ""
  ip_range_services          = ""
  http_load_balancing        = false
  horizontal_pod_autoscaling = false
  network_policy             = true

  node_pools = [
    {
      name               = "core-pool"
      machine_type       = "n1-highmem-2"
      min_count          = 1
      max_count          = 10
      local_ssd_count    = 0
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "ubuntu"
      auto_repair        = true
      auto_upgrade       = false
      preemptible        = false
      initial_node_count = 1
    },
    {
      name               = "user-pool-2020-09-29"
      machine_type       = "n1-highmem-4"
      min_count          = 1
      max_count          = 10
      local_ssd_count    = 0
      disk_size_gb       = 200
      disk_type          = "pd-standard"
      image_type         = "ubuntu"
      auto_repair        = true
      auto_upgrade       = false
      preemptible        = false
      initial_node_count = 1
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
      default-node-pool = true
      "hub.jupyter.org/pool-name" = "core-pool"
    }
    user-pool-2020-09-29 = {
      "hub.jupyter.org/pool-name" = "user-pool"
    }
  }
}
