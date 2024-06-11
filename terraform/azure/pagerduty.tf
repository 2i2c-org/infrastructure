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
  name                = "AlertsActionGroup"  # Changing this forces a recreation
  resource_group_name = var.resourcegroup_name
  short_name          = "alertaction"

  webhook_receiver {
    name        = "callpagerdutyapi"
    service_uri = "https://events.pagerduty.com/integration/5ebdc22d2399400cd0560e450b579333/enqueue"
  }
}

