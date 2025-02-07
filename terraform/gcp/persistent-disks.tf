resource "google_compute_disk" "nfs_homedirs" {
  for_each = var.persistent_disks

  zone    = var.zone
  project = var.project_id

  name = each.value.name_suffix == null ? "hub-nfs-homedirs" : "hub-nfs-homedirs-${each.value.name_suffix}"
  size = each.value.size
  type = each.value.type

  labels = each.value.tags

  lifecycle {
    prevent_destroy = true
  }
}

output "persistent_disk_id_map" {
  value = { for pd in values(google_compute_disk.nfs_homedirs)[*] : pd.name => { "id": pd.id, "disk_id": pd.disk_id } }
}
