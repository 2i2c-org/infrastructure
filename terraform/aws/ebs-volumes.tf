resource "aws_ebs_volume" "nfs_home_dirs" {
  for_each = var.ebs_volumes

  availability_zone = var.cluster_nodes_location
  size              = each.value.size
  type              = each.value.type
  iops              = each.value.iops
  encrypted         = true

  tags = merge(each.value.tags, {
    Name                  = each.value.name_suffix == null ? "hub-nfs-home-dirs" : "hub-nfs-home-dirs-${each.value.name_suffix}"
    "2i2c:volume-purpose" = "home-nfs"
    NFSBackup             = var.enable_nfs_backup ? "true" : "false" # Tag to identify volumes to backup by Data Lifecycle Manager (DLM)
  })

  lifecycle {
    prevent_destroy = true
  }
}

data "sops_file" "pagerduty_volume_integration" {
  # Read sops encrypted file containing integration key for pagerduty
  source_file = "secret/enc-pagerduty-volume-integration.yaml"
}

resource "aws_sns_topic" "volume_metric_exceeded" {
  name = "volume-metric-exceeded-topic"
}

resource "aws_sns_topic_subscription" "volume_metric_exceeded_https_target" {
  topic_arn = aws_sns_topic.volume_metric_exceeded.arn
  protocol  = "https"
  endpoint  = data.sops_file.pagerduty_volume_integration.data["pagerdutyIntegration.url"]
}

resource "aws_cloudwatch_metric_alarm" "volume_throughput_alarm" {
  alarm_name                = "warn-volume-throughput-exceeded"
  comparison_operator       = "GreaterThanThreshold"
  evaluation_periods        = 1
  metric_name               = "VolumeThroughputExceededCheck"
  namespace                 = "AWS/EBS"
  period                    = 300
  statistic                 = "Average"
  threshold                 = 0.7
  alarm_description         = "This metric monitors disk throughput"
  insufficient_data_actions = []
  alarm_actions             = [aws_sns_topic.volume_metric_exceeded.arn]
}

resource "aws_cloudwatch_metric_alarm" "volume_iops_alarm" {
  alarm_name                = "warn-volume-iops-exceeded"
  comparison_operator       = "GreaterThanThreshold"
  evaluation_periods        = 1
  metric_name               = "VolumeIOPSExceededCheck"
  namespace                 = "AWS/EBS"
  period                    = 300
  statistic                 = "Average"
  threshold                 = 0.7
  alarm_description         = "This metric monitors disk IOPs"
  insufficient_data_actions = []
  alarm_actions             = [aws_sns_topic.volume_metric_exceeded.arn]
}

output "ebs_volume_id_map" {
  value = { for vol in values(aws_ebs_volume.nfs_home_dirs)[*] : vol.tags["Name"] => vol.id }
}
