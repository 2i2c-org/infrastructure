# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/subscription
data "azurerm_subscription" "current" {}

# ref: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/consumption_budget_subscription
resource "azurerm_consumption_budget_subscription" "budget" {
  count = var.budget_alert_enabled ? 1 : 0

  name            = "BudgetSubscription-${var.resourcegroup_name}"
  subscription_id = data.azurerm_subscription.current.id

  amount     = var.budget_alert_amount
  time_grain = "Monthly"

  time_period {
    start_date = "2024-07-01T00:00:00Z"
    end_date   = "2029-07-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 120
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"

    contact_emails = [
      "support+budget-${var.resourcegroup_name}@2i2c.org",
    ]
  }
}
