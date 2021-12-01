resource "azuread_service_principal" "service_principal" {
  application_id               = var.subscription_id
  app_role_assignment_required = false
  use_existing                 = true
}

resource "azuread_service_principal_password" "service_principal_password" {
  service_principal_id = azuread_service_principal.service_principal.object_id
}
