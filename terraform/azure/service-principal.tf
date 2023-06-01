resource "azuread_service_principal" "service_principal" {
  count = var.create_service_principal ? 1 : 0

  application_id               = var.subscription_id
  app_role_assignment_required = false
  use_existing                 = true
}

resource "azuread_service_principal_password" "service_principal_password" {
  count = var.create_service_principal ? 1 : 0

  service_principal_id = azuread_service_principal.service_principal[0].object_id
}

locals {
  service_principal = {
    "tenant_id" : var.tenant_id,
    "subscription_id" : var.subscription_id,
    "service_principal_id" : var.create_service_principal ? azuread_service_principal.service_principal[0].object_id : "",
    "service_principal_password" : var.create_service_principal ? azuread_service_principal_password.service_principal_password[0].value : ""
  }
}

output "service_principal_config" {
  value     = jsonencode(local.service_principal)
  sensitive = true
}
