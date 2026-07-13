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

resource "aws_budgets_budget" "threshold_budgets" {
  for_each = var.budget_alerts

  name         = "Budget ${each.key} for ${var.cluster_name}"
  budget_type  = "COST"
  limit_unit   = "USD"
  limit_amount = each.value.max_cost
  time_unit    = each.value.time_period

  dynamic "notification" {
    for_each = ["20", "40", "60", "80", "90", "100", "120"]
    iterator = threshold
    content {
      comparison_operator = "GREATER_THAN"
      threshold           = threshold.value
      threshold_type      = "PERCENTAGE"
      notification_type   = "ACTUAL"
      subscriber_email_addresses = concat([
        "support+${var.cluster_name}@2i2c.org"
      ], each.value.emails)
    }
  }
}
