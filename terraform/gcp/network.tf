/**
* Networking to support private clusters
*
* This config is only deployed when the enable_private_cluster variable is set
* to true
*/

resource "google_compute_network" "vpc_network" {
  count = var.enable_private_cluster ? 1 : 0

  name                    = "${var.prefix}-vpc-network"
  project                 = var.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnetwork" {
  count = var.enable_private_cluster ? 1 : 0

  name                     = "${var.prefix}-subnetwork"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.vpc_network[0].id
  private_ip_google_access = true

  // Decide if this is a sensible IP CIDR range or not
  ip_cidr_range = "10.2.0.0/16"
}

resource "google_compute_firewall" "firewall_rules" {
  count = var.enable_private_cluster ? 1 : 0

  name    = "allow-ssh"
  project = var.project_id
  network = google_compute_network.vpc_network[0].name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}
