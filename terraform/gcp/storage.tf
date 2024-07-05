resource "google_filestore_instance" "homedirs" {

  name     = var.filestores[count.index].name_suffix == null ? "${var.prefix}-homedirs" : "${var.prefix}-homedirs-${var.filestores[count.index].name_suffix}"
  location = var.zone
  tier     = var.filestores[count.index].tier
  project  = var.project_id

  count = length(var.filestores)

  lifecycle {
    # Additional safeguard against deleting the filestore
    # as this causes irreversible data loss!
    prevent_destroy = true
  }

  file_shares {
    capacity_gb = var.filestores[count.index].capacity_gb
    name        = "homes"
  }

  networks {
    network = var.enable_private_cluster ? data.google_compute_network.default_network.name : "default"
    modes   = ["MODE_IPV4"]
  }
}
