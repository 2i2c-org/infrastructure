resource "azurerm_consumption_budget_resource_group" "budget" {
  name              = "BudgetResourceGroup"
  resource_group_id = azurerm_resource_group.jupyterhub.id

  amount     = var.budget_alert_amount
  time_grain = "Monthly"

  time_period {
    start_date = "2024-07-01T00:00:00Z"
    end_date   = "2029-07-01T00:00:00Z"
  }

  notification {
    enabled        = var.budget_alert_enabled ? true : false
    threshold      = 120
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"

    contact_emails = [
      "support+budget-${var.resourcegroup_name}@2i2c.org",
    ]
  }
}
