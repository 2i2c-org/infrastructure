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
  value = { for pd in values(google_compute_disk.nfs_homedirs)[*] : pd.name => pd.id }
}

resource "google_compute_resource_policy" "snapshot_schedule" {
  for_each = { for k, v in var.persistent_disks : k => v if v.disable_nfs_backups != true }

  name    = "hub-nfs-homedirs-${each.value.name_suffix}-snapshot-schedule"
  region  = var.region
  project = var.project_id

  snapshot_schedule_policy {
    schedule {
      daily_schedule {
        days_in_cycle = 1
        start_time    = "00:00"
      }
    }
    retention_policy {
      max_retention_days = each.value.max_retention_days
    }
  }
}

resource "google_compute_disk_resource_policy_attachment" "snapshot_schedule_policy_attachment" {
  for_each = { for k, v in var.persistent_disks : k => v if v.disable_nfs_backups != true }

  name = google_compute_resource_policy.snapshot_schedule[each.value.name_suffix].name
  disk = google_compute_disk.nfs_homedirs[each.value.name_suffix].name

  project = var.project_id
  zone    = var.zone
}
