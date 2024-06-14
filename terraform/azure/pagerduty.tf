/**
* This file defines alerts and notification channels for sending information to
* PagerDuty in order to trigger incidents. This relies on pre-registered
* PagerDuty services with "Microsoft Azure" integrations in 2i2c's PagerDuty
* account.
*
* - PagerDuty services in 2i2c's PagerDuty account:
*   https://2i2c-org.pagerduty.com/service-directory/?direction=asc&query=&team_ids=all
*
*/
data "sops_file" "pagerduty_service_integration_keys" {
  # Read sops encrypted file containing integration key for pagerduty
  source_file = "secret/enc-pagerduty-service-integration-keys.secret.yaml"
}

resource "azurerm_monitor_action_group" "alerts" {
  name                = "AlertsActionGroup" # Changing this forces a recreation
  resource_group_name = var.resourcegroup_name
  short_name          = "alertaction"

  webhook_receiver {
    name        = "callpagerdutyapi"
    service_uri = data.sops_file.pagerduty_service_integration_keys.data["disk_space_service_uri"]
  }
}

resource "azurerm_monitor_metric_alert" "disk_space_full_alert" {
  # Changing the name forces a recreation every time we apply
  name                = "Used disk space approaching capacity on Azure Subscription ${var.subscription_id}"
  resource_group_name = var.resourcegroup_name
  scopes              = [azurerm_storage_account.homes.id]
  description         = "Action will be triggered when used disk space is greater than ${local.storage_threshold} GB."

  window_size = "PT1H" # Window to aggregate over: 1 Hour

  criteria {
    metric_namespace = "Microsoft.Storage/storageAccounts"
    metric_name      = "UsedCapacity"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = local.storage_threshold * 1000000000 # Convert GB to Bytes
  }

  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }
}
