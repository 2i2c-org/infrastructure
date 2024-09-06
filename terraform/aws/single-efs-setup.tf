// Original setup for a single, cluster-wide EFS instance.
// FIXME: To be deleted once all the clusters have been migrated
//        to use aws_efs_file_system.homedirs_map instead
//        and var.disable_cluster_wide_filestore was set to true
resource "aws_efs_file_system" "homedirs" {
  count = var.disable_cluster_wide_filestore ? 0 : 1

  tags = merge(var.original_single_efs_tags, { Name = "hub-homedirs" })

  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  lifecycle_policy {
    transition_to_ia = "AFTER_90_DAYS"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_efs_mount_target" "homedirs" {
  for_each = var.disable_cluster_wide_filestore ? [] : toset(data.aws_subnets.cluster_node_subnets.ids)

  file_system_id  = one(aws_efs_file_system.homedirs[*].id)
  subnet_id       = each.key
  security_groups = [data.aws_security_group.cluster_nodes_shared_security_group.id]
}

output "nfs_server_dns" {
  value = var.disable_cluster_wide_filestore ? 0 : one(aws_efs_file_system.homedirs[*].dns_name)
}

resource "aws_efs_backup_policy" "homedirs" {
  count = var.disable_cluster_wide_filestore ? 0 : 1

  file_system_id = one(aws_efs_file_system.homedirs[*].id)
  backup_policy {
    status = "ENABLED"
  }
}
