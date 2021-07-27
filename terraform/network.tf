/**
* Networking to support private clusters
*
* This config is only deployed when the enable_private_cluster variable is set
* to true
*/

// Deploy a VPC: https://cloud.google.com/vpc
module "vpc_module" {
  source  = "terraform-google-modules/network/google"
  version = "~> 3.3.0"

  count = var.enable_private_cluster ? 1 : 0

  project_id   = var.project_id
  network_name = "${var.prefix}-vpc-network"

  subnets = [
    {
      // Decide if this subnet IP range is sensible or not
      subnet_ip     = "192.168.1.0/24"
      subnet_name   = "${var.prefix}-${var.region}-subnet"
      subnet_region = var.region
    }
  ]
}

// Set a firewall rule that allows SSH
resource "google_compute_firewall" "firewall_rules" {
  count = var.enable_private_cluster ? 1 : 0

  project = var.project_id
  name    = "allow-ssh"
  network = module.vpc_module[0].network_self_link

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

// Deploy a router: https://cloud.google.com/network-connectivity/docs/router
resource "google_compute_router" "router" {
  count = var.enable_private_cluster ? 1 : 0

  project = var.project_id
  name    = "${var.prefix}-router"
  network = module.vpc_module[0].network.network_self_link
  region  = var.region
}

// Deploy a Cloud NAT (network address translation):
// https://cloud.google.com/nat/docs/overview
module "cloud-nat" {
  count = var.enable_private_cluster ? 1 : 0

  source     = "terraform-google-modules/cloud-nat/google"
  version    = "~> 2.0.0"
  project_id = var.project_id
  name       = "${var.prefix}-cloud-nat"
  region     = var.region
  router     = google_compute_router.router[0].name

  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
