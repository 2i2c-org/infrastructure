# Setup Domain Redirects

Sometimes, when we move a hub, we want to redirect users from the
old hub to the new hub. While this will still break users *currently*
on the hub, it should work seamlessly for anyone trying to login.

You can set up redirects by adding something like this to the appropriate
`support.values.yaml` file for the *cluster* the hub is on:

```yaml
redirects:
  rules:
    - from: <old-hub-domain>
      to: <new-hub-domain>
```

You can add any number of such redirects. They will all be `302 Temporary`
redirects, in case we want to re-use the old domain for something else in
the future.
