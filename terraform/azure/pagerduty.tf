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

