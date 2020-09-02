terraform {
  backend "gcs" {
    bucket  = "2i2c-terraform-state"
    prefix  = "terraform/state/similar-hubs"
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
      "${var.project_id}=>roles/container.admin"
  ]
}

output "ci_deployer_key" {
  value = module.service_accounts.keys["cd-sa"]
}

module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  project_id                 = var.project_id
  name                       = "${var.prefix}-cluster"
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
      machine_type       = "e2-medium"
      min_count          = 1
      max_count          = 10
      local_ssd_count    = 0
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "ubuntu"
      auto_repair        = true
      auto_upgrade       = true
      preemptible        = false
      initial_node_count = 1
    },
  ]

  node_pools_oauth_scopes = {
    all = []

    core-pool = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  node_pools_labels = {
    all = {}

    core-pool = {
      default-node-pool = true
      "hub.jupyter.org/pool-name" = "core-pool"
    }
  }
}