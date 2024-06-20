resource "google_filestore_instance" "homedirs" {

  name     = "${var.prefix}-homedirs"
  location = var.zone
  tier     = var.filestore_tier
  project  = var.project_id

  count = var.enable_filestore ? 1 : 0

  lifecycle {
    # Additional safeguard against deleting the filestore
    # as this causes irreversible data loss!
    prevent_destroy = true
  }

  file_shares {
    capacity_gb = var.filestore_capacity_gb
    name        = "homes"
  }

  networks {
    network = google_compute_network.network.name
    modes   = ["MODE_IPV4"]
  }
}
