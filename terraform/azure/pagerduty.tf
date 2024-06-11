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
    service_uri = "https://events.pagerduty.com/integration/5ebdc22d2399400cd0560e450b579333/enqueue"
  }
}

resource "azurerm_monitor_metric_alert" "disk_space_full_alert" {
  name                = "Used disk space > ${local.storage_threshold} GB on ${var.subscription_id}"
  resource_group_name = var.resourcegroup_name
  scopes              = [azurerm_storage_account.homes.id]
  description         = "Action will be triggered when used disk space is > ${local.storage_threshold} GB."

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