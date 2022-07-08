# Deploy authenticated static websites along the hub

We can deploy *authenticated* static websites on the same domain as the hub
that is only accessible to users who have access to the hub. The source
for these come from git repositories that should contain rendered HTML,
and will be updated every 5 minutes. They can be under any prefix on the
same domain as the hub (such as `/docs`, `/textbook`, etc).

You can enable this with the following config in the `.values.yaml`
file for your hub.

```yaml

dex:
  # Enable authentication
  enabled: true
  hubHostName: <hostname-of-hub>

staticSites:
  enabled: true
  repo: <url-of-git-repo>
  branch: <name-of-git-branch>
  host: <hostname-of-hub>
  path: <absolute-path-where-content-is-available>

jupyterhub:
  hub:
    services:
      dex:
        url: http://dex:5556
        oauth_redirect_url: https://<hostname-of-hub>/services/dex/callback
        oauth_no_confirm: true
        display: false
      oauth2-proxy:
        display: false
        url: http://dex:9000

```

```{note}
We manually configure the hub services instead of autogenerating
them in our deploy scripts. This leads to some additional copy-pasting and
duplication, but keeps our config explicit and simple.
```

## Example

Here's a sample that hosts the data8 textbook under `https://staging.2i2c.cloud/textbook`:

```yaml
dex:
  enabled: true
  hubHostName: staging.2i2c.cloud

staticSites:
  enabled: true
  repo: https://github.com/inferentialthinking/inferentialthinking.github.io
  branch: master
  host: staging.2i2c.cloud
  path: /textbook

jupyterhub:
  hub:
    services:
      dex:
        url: http://dex:5556
        oauth_redirect_uri: https://staging.2i2c.cloud/services/dex/callback
        oauth_no_confirm: true
      oauth2-proxy:
        url: http://dex:9000
```

This clones the [repo]( https://github.com/inferentialthinking/inferentialthinking.github.io),
checks out the `master` branch and keeps it up to date by doing a
`git pull` every 5 minutes. It is made available under `/textbook`,
and requires users be logged-in to the hub before they can access it.

### Note on relative URLs

Depending on what Static Site Generator has been used to generate the website's static content, it **may** or **may not** use relative paths routing by default.
For example, [Sphinx](https://www.sphinx-doc.org/en/master/) handles relative paths by default, whereas, [Hugo](https://gohugo.io/) leaves all [relative URLs unchanged](https://gohugo.io/content-management/urls/#relative-urls).

However, having relative URLS is a **must** in order for the hub docs service to work. Please check with the docs of your SSG of choice and enable relative URLs if they
aren't enabled already.
```