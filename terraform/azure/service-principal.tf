resource "azuread_service_principal" "service_principal" {
  application_id               = var.subscription_id
  app_role_assignment_required = false
  use_existing                 = true
}

resource "azuread_service_principal_password" "service_principal_password" {
  service_principal_id = azuread_service_principal.service_principal.object_id
}

locals{
  service_principal = {
    "tenant_id": var.tenant_id,
    "subscription_id": var.subscription_id,
    "service_principal_id": azuread_service_principal.service_principal.object_id,
    "service_principal_password": azuread_service_principal_password.service_principal_password.value
  }
}

output "service_principal_config" {
  value     = jsonencode(local.service_principal)
  sensitive = true
}
