# Alerts sent to support@2i2c.org for things that *will go bad* in the future
# if left unattended. Should *not* be used for immediate outages

resource "google_monitoring_notification_channel" "support_email" {
  count        = var.budget_alert_enabled ? 1 : 0
  project      = var.project_id
  display_name = "support@2i2c.org email"
  type         = "email"
  labels = {
    email_address = "support@2i2c.org"
  }
}

data "google_project" "project" {
  project_id = var.project_id
}

# Need to explicitly enable https://console.cloud.google.com/apis/library/billingbudgets.googleapis.com?project=two-eye-two-see
resource "google_billing_budget" "budget" {
  count = var.budget_alert_enabled ? 1 : 0

  billing_account = var.billing_account_id
  display_name    = "Billing alert"

  budget_filter {
    # Use project number here, as project_name seems to be converted internally to number
    # If we don't do this, `terraform apply` is not clean
    # This is a bug in the google provider / budgets API https://github.com/hashicorp/terraform-provider-google/issues/8444
    projects               = ["projects/${data.google_project.project.number}"]
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = var.budget_alert_currency
      units         = var.budget_alert_amount
    }
  }

  all_updates_rule {
    monitoring_notification_channels = [
      google_monitoring_notification_channel.support_email[0].id,
    ]
    disable_default_iam_recipients = true
  }
  # NOTE: These threshold_rules *MUST BE ORDERED BY threshold_percent* in ascending order!
  # If not, we'll run into https://github.com/hashicorp/terraform-provider-google/issues/8444
  # and terraform apply won't be clean.
  threshold_rules {
    # Alert when *actual* spend reached 80% of budget
    threshold_percent = 0.8
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    # Alert when *forecasted* spend is about to blow over our budget
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

}
