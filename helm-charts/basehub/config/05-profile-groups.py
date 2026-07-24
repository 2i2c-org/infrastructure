# Re-assignes c.KubeSpawner.profile_list to a callable that filters the
# initial configuration of profile_list based on the user's github
# org/team membership as declared via "allowed_groups" read from
# profile_list profiles.
#
# This only has effect if:
#
# - GitHubOAuthenticator is used.
# - GitHubOAuthenticator.populate_teams_in_auth_state is True, that
#   requires Authenticator.enable_auth_state to be True as well.
# - The user is a normal user, and not "deployment-service-check".
#
from copy import deepcopy
from functools import partial
from textwrap import dedent

from oauthenticator.github import GitHubOAuthenticator
from tornado import web


async def profile_list_allowed_groups_filter(original_profile_list, spawner):
    """
    Returns the initially configured profile_list filtered based on the
    user's membership in each profile's `allowed_groups`. If
    `allowed_groups` isn't set for a profile, that profile is allowed for
    everyone. Similar functionality is provided for both `unlisted_choice` and
    `choice` inside `profile_options`.

    `allowed_groups` is a list of JupyterHub groups, set up by the authenticator.
    In addition, for use with GitHubOAuthenticator, it can be a list of
    teams the user is a part of, of form '<github-org>:<team-name>'.

    If the returned profile_list is filtered to not include any profiles,
    an error is raised and the user isn't allowed to start a server.
    """
    if spawner.user.name == "deployment-service-check":
        print("Ignoring allowed_groups check for deployment-service-check")
        return original_profile_list

    # casefold group names so we can do case insensitive comparisons.
    groups = {g.name.casefold() for g in spawner.user.groups}

    # If we're using GitHubOAuthenticator, add the user's teams to the groups as well.
    # Eventually this can be removed, as the user's teams can be set to be groups
    # once https://github.com/jupyterhub/oauthenticator/pull/735 is merged
    if isinstance(spawner.authenticator, GitHubOAuthenticator):
        # Ensure auth_state is populated with teams info
        auth_state = await spawner.user.get_auth_state()
        if not auth_state or "teams" not in auth_state:
            print(
                f"User {spawner.user.name} does not have any auth_state set, profile_list filtering not available"
            )

        else:
            # casefold teams to match what GitHub's API does when doing authorization calls
            groups |= {
                f"{team['organization']['login']}:{team['slug']}".casefold()
                for team in auth_state["teams"]
            }

    print(f"User {spawner.user.name} is part of groups {' '.join(groups)}")

    # Filter out profiles with allowed_groups set if the user isn't part of the group
    allowed_profiles = []
    for original_profile in original_profile_list:
        # Make a copy, as we'll be modifying this profile
        profile = deepcopy(original_profile)

        # Handle `allowed_groups` specified in profile_options
        if "profile_options" in profile:
            for k, po in profile["profile_options"].items():
                # If `unlisted_choice` has an `allowed_groups` and the current
                # user is not present in any of those teams, we delete the
                # `unlisted_choice` config entirely for this option. The user
                # will then not be allowed to 'write in' a value.
                if "unlisted_choice" in po:
                    if "allowed_groups" in po["unlisted_choice"]:
                        if not (set(po["unlisted_choice"]["allowed_groups"]) & groups):
                            del po["unlisted_choice"]

                if "choices" in po:
                    new_choices = {}
                    for k, c in po["choices"].items():
                        # If `allowed_groups` is not set for a profile option, it is automatically
                        # allowed for everyone
                        if "allowed_groups" not in c:
                            new_choices[k] = c
                        # If `allowed_groups` *is* set for a profile option, it is allowed only for
                        # members of that team.
                        else:
                            allowed_groups = {g.casefold() for g in c["allowed_groups"]}
                            if allowed_groups & groups:
                                new_choices[k] = c
                    po["choices"] = new_choices

        if "allowed_groups" not in profile:
            allowed_profiles.append(profile)
        else:
            allowed_groups = {g.casefold() for g in profile.get("allowed_groups", [])}

            if allowed_groups & groups:
                print(
                    f"Allowing profile {profile['display_name']} for user {spawner.user.name} based on team membership"
                )
                allowed_profiles.append(profile)
                continue

    if len(allowed_profiles) == 0:
        # If no profiles are allowed, user should not be able to spawn anything!
        # If we don't explicitly stop this, user will be logged into the 'default' settings
        # set in singleuser, without any profile overrides. Not desired behavior
        # FIXME: User doesn't actually see this error message, just the generic 403.
        error_msg = dedent(f"""
        Your JupyterHub group membership is insufficient to launch any server profiles.

        JupyterHub groups you are a member of are {", ".join(groups)}.

        If you are part of additional groups, log out of this JupyterHub and log back in to refresh that information.
        """)
        raise web.HTTPError(403, error_msg)

    return allowed_profiles


# Only set our custom filter if
# profile_list is specified (otherwise users will get an empty screen when trying to launch servers)
if c.KubeSpawner.profile_list:
    # Customize list of profiles dynamically, rather than override options form.
    # This is more secure, as users can't override the options available to them via the hub API
    # We pass in a copy of the original profile_list set in config via partial, to reduce possible variable
    # capture related issues.
    c.KubeSpawner.profile_list = partial(
        profile_list_allowed_groups_filter, deepcopy(c.KubeSpawner.profile_list)
    )
