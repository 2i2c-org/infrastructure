resource "google_filestore_instance" "homedirs" {
  for_each = var.filestores

  name     = each.value.name_suffix == null ? "${var.prefix}-homedirs" : "${var.prefix}-homedirs-${each.value.name_suffix}"
  location = var.zone
  tier     = each.value.tier
  project  = var.project_id

  lifecycle {
    # Additional safeguard against deleting the filestore
    # as this causes irreversible data loss!
    prevent_destroy = true
  }

  file_shares {
    capacity_gb   = each.value.capacity_gb
    name          = "homes"
    source_backup = each.value.source_backup
  }

  networks {
    network = "default"
    modes   = ["MODE_IPV4"]
  }
}
