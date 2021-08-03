/**
* Networking to support private clusters
*
* This config is only deployed when the enable_private_cluster variable is set
* to true
*/

data "google_compute_network" "default_network" {
  name    = "default"
  project = var.project_id
}

data "google_compute_subnetwork" "default_subnetwork" {
  name    = "default"
  project = var.project_id
  region  = var.region
}

resource "google_compute_firewall" "iap_ssh_ingress" {
  count = var.enable_private_cluster ? 1 : 0

  name    = "allow-ssh"
  project = var.project_id
  network = data.google_compute_network.default_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  // This range contains all IP addresses that IAP uses for TCP forwarding.
  // https://cloud.google.com/iap/docs/using-tcp-forwarding
  source_ranges = ["35.235.240.0/20"]
}

resource "google_compute_router" "router" {
  count = var.enable_private_cluster ? 1 : 0

  name    = "${var.prefix}-router"
  project = var.project_id
  region  = var.region
  network = data.google_compute_network.default_network.id
}

resource "google_compute_router_nat" "nat" {
  count = var.enable_private_cluster ? 1 : 0

  name                               = "${var.prefix}-router-nat"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.router[0].name
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
