resource "aws_budgets_budget" "budgets" {
  count = var.default_budget_alert.enabled ? 1 : 0

  name        = "Auto-adjusting budget for ${var.cluster_name}"
  budget_type = "COST"
  limit_unit  = "USD"
  time_unit   = "MONTHLY"

  auto_adjust_data {
    auto_adjust_type = "HISTORICAL"

    historical_options {
      budget_adjustment_period = 3
    }
  }

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 120
    threshold_type      = "PERCENTAGE"
    notification_type   = "FORECASTED"
    subscriber_email_addresses = [
      for email in var.default_budget_alert.subscriber_email_addresses :
      replace(email, "{var_cluster_name}", var.cluster_name)
    ]
  }
}
