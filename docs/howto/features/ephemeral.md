# Make an ephemeral hub

We can support users who want a [mybinder.org](https://mybinder.org)
type experience, but with better resources & faster startup. They get
redirected to us when the public mybinder.org deployment can not
support them ([like this](https://github.com/jupyterhub/mybinder.org-deploy/issues/2534)),
or just because they want this experience.

The primary features offered would be:

1. No *per-user authentication* required.
2. A shared, systemwide *password* is present to protect against cryptobros
   abusing these resources.
3. No *persistent storage*
4. Pre-pulled images, for faster startup.

(1) and (3) also help reduce the amount of user data we store, reducing data
privacy issues as well.

The limitations of this set up are:

1. No users means no *admin users*, so the JupyterHub configurator is unavailable.
   All config must be set in our config files, and deployed via GitHub.
2. No home page is visible, so our home page customizations do not work.
3. We do *not* cull users, because that would [cause problems](https://blog.jupyter.org/accurately-counting-daily-weekly-monthly-active-users-on-jupyterhub-6fbec6c6ce2f)
   with counting active users. This is a trade-off, as if we end up with a *huge*
   list of users, it might slow down hub deployments.

## Authentication with `tmpauthenticator`

We will use [tmpauthenticator](https://github.com/jupyterhub/tmpauthenticator)
to automatically create temporary users whenever any user comes to the hub.
They will automatically get UUIDs assigned.

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: tmpauthenticator.TmpAuthenticator
      TmpAuthenticator:
        # This allows users to go to the hub URL directly again to
        # get a new server, instead of being plopped back into their
        # older, existing user with a 'start server' button.
        force_new_server: true
```

## Shared systemwide password setup

Unfortunately, a shared password is required to guard against random cryptobros
abusing using our systems for 'free' compute. This password is same for all
users, and can be shared by the community champions of the hub in whatever
form they wish.

This requires two bits of config - one in the `<hub>.values.yaml` file for the hub,
and another in the `enc-<hub>.secret.values.yaml` file.

In `<hub>.values.yaml`:

```yaml
ingressBasicAuth:
  enabled: true
  
jupyterhub:
  ingress:
    annotations:
      # We protect our entire hub from cryptobros by putting it all
      # behind a single shared basicauth
      nginx.ingress.kubernetes.io/auth-type: basic
      nginx.ingress.kubernetes.io/auth-secret: ingress-basic-auth
      nginx.ingress.kubernetes.io/auth-realm: "Authentication Required"
```

In `enc-<hub>.secret.values.yaml`:
```yaml
ingressBasicAuth:
  username: <username>
  password: <password>
```

```{tip}
Pick a *passphrase* for the password, like [the holy book says](https://xkcd.com/936/).
```

```{note}
Make sure the `enc-<hub>.secret.values.yaml` is encrypted via [sops](tools:sops)
```

## No persistent storage

As users are temporary and can not be accessed again, there is no reason to
provide persistent storage. So we turn it all off.

```yaml
jupyterhub:
  custom:
    singleuserAdmin:
      # Turn off trying to mount shared-readwrite folder for admins
      extraVolumeMounts: []
  singleuser:
    initContainers: []
    storage:
      # No persistent storage should be kept to reduce any potential data
      # retention & privacy issues.
      type: none
      extraVolumeMounts: []
```


## Pre-pulled images

We want *consistently* faster startups wherever possible, as inconsistent start
times is one of the big issues with folks using mybinder.org for events and
workshops. So we enable the [pre-puller](https://z2jh.jupyter.org/en/latest/administrator/optimization.html#pulling-images-before-users-arrive)
functionality to make startups faster and more consistent.

This requires the user image is also set in config (and not via the JupyterHub
configurator). But `tmpauthenticator` doesn't support admin accounts anyway,
so this is fine.

```yaml
jupyterhub:
  singleuser:
    image:
      name: <image-name>
      tag: <tag>
      
  prePuller:
    # Startup performance is important for this event, and so we use
    # pre-puller to make sure the images are already present on the
    # nodes. This means image *must* be set in config, and not the configurator.
    # tmpauthenticator doesn't support admin access anyway, so images
    # must be set in config regardless.
    hook:
      enabled: true
    continuous:
      enabled: true
```

## Disabling home page customizations

`tmpauthenticator` doesn't actually show the home page - it just launches
users directly into the notebook server. This means our home page customizations
are not applied anywhere. So we set them to empty strings.

```yaml
jupyterhub:
  custom:
    homepage:
      # tmpauthenticator does *not* show a home page by default,
      # so these are not visible anywhere. But our schema requires we set
      # them to strings, so we specify empty strings here.
      templateVars:
        org:
          name: ""
          url: ""
          logo_url: ""
        designed_by:
          name: ""
          url: ""
        operated_by:
          name: ""
          url: ""
        funded_by:
          name: ""
          url: ""
```


## Customizing the uptime check to expect a HTTP `401`

Our [uptime checks](uptime-checks) expect a HTTP `200` response to consider a
hub as live. However, since we protect the entire hub at the Ingress level,
all endpoints will return a HTTP `401` asking for a password. We can configure
our uptime checks to allow for `401` as a valid response in the appropriate
`cluster.yaml` definition for this hub.

```yaml
  - name: <name-of-hub>
    display_name: <display-name>
    uptime_check:
      # This is an ephemeral hub, fully password protected with HTTP Basic Auth
      expected_status: 401
```

## Use `nbgitpuller` for distributing content

We encourage users to use [nbgitpuller](https://github.com/jupyterhub/nbgitpuller)
for distributing content. This allows creation of a specific link that will
put users who click it on a specific notebook with a specific UI (such as lab,
classic notebook, RStudio, etc).

The [http://nbgitpuller.link/](nbgitpuller link generator) supports mybinder.org
style links, but for use with *ephemeral hubs*, just use the regular 'JupyterHub'
link generator. [Firefox](https://addons.mozilla.org/en-US/firefox/addon/nbgitpuller-link-generator/)
and [Google Chrome](https://chrome.google.com/webstore/detail/nbgitpuller-link-generato/hpdbdpklpmppnoibabdkkhnfhkkehgnc)
extensions are also available.
