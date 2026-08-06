def refresh_user_hook(authenticator, user, auth_state):
    if user.name == "deployment-service-check":
        # if this is the user,
        # refresh_user doesn't make sense
        # consider it always fresh
        return True
    # for all other users, refresh as usual
    return None


c.OAuthenticator.refresh_user_hook = refresh_user_hook
