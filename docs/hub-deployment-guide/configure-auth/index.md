(enable-auth-provider)=
# Enable authentication

This section describes how to set up various authentication providers for the 2i2c JupyterHubs.

```{admonition} Switching auth
Switching authentication providers (e.g. from GitHub to Google) for a pre-existing hub will simply create new usernames. Any pre-existing users will no longer be able to access their accounts (although administrators will be able to do so). If you have pre-existing users and want to switch the hub authentication, rename the users to the new auth pattern (e.g. convert github handles to emails).
```

```{toctree}
:maxdepth: 2
:caption: Authentication Providers
github-orgs
cilogon
```
