from z2jh import get_config

add_staff_user_ids_to_admin_users = get_config(
    "custom.2i2c.add_staff_user_ids_to_admin_users", False
)

if add_staff_user_ids_to_admin_users:
    user_id_type = get_config("custom.2i2c.add_staff_user_ids_of_type")
    staff_user_ids = get_config(f"custom.2i2c.staff_{user_id_type}_ids", [])
    # `c.Authenticator.admin_users` can contain additional admins, can be an empty list,
    # or it cannot be defined at all.
    # This should cover all these cases.
    staff_user_ids.extend(get_config("hub.config.Authenticator.admin_users", []))
    c.Authenticator.admin_users = staff_user_ids

# Appends 2i2c staff access by GitHub team membership by default for GitHub authenticated hubs.
if (
    c.JupyterHub.authenticator_class == "github"
    and type(c.GitHubOAuthenticator.allowed_organizations) == list
):
    c.GitHubOAuthenticator.allowed_organizations.append(
        "2i2c-org:hub-access-for-2i2c-staff"
    )
elif c.JupyterHub.authenticator_class == "github":
    print(
        "No GitHubOAuthenticator.allowed_organizations found, setting to ['2i2c-org:hub-access-for-2i2c-staff']"
    )
    c.GitHubOAuthenticator.allowed_organizations = [
        "2i2c-org:hub-access-for-2i2c-staff"
    ]
