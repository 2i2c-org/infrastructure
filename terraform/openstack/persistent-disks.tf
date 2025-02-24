resource "openstack_blockstorage_volume_v3" "nfs_home_dirs" {
  for_each = var.persistent_disks

  name                 = each.value.name_suffix == null ? "hub-nfs-homedirs" : "hub-nfs-homedirs-${each.value.name_suffix}"
  size                 = each.value.size
  metadata             = each.value.tags
  enable_online_resize = true

  lifecycle {
    prevent_destroy = true
  }
}

output "persistent_disk_id_map" {
  value = { for vol in values(openstack_blockstorage_volume_v3.nfs_home_dirs)[*] : vol.name => vol.id }
}

