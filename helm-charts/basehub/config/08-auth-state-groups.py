# Pass the user's GitHub teams from auth_state to JupyterHub group memberships.


async def custom_auth_state_groups_key(auth_state):
    if "teams" not in auth_state.keys():
        print("No GitHub teams found in auth_state.")
        return None
    else:
        groups_list = []
        for team in auth_state["teams"]:
            if (
                f"{team['organization']['login']}:{team['slug']}"
                not in c.GitHubOAuthenticator.allowed_organizations
            ):
                continue
            else:
                groups_list.append(f"{team['organization']['login']}:{team['slug']}")
        custom_auth_state_groups_key.groups_list = groups_list
        return groups_list


if c.JupyterHub.authenticator_class == "github":
    c.GitHubOAuthenticator.auth_state_groups_key = custom_auth_state_groups_key
