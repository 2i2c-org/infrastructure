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
        authenticator_class: tmp
```


## No persistent home directory

As users are temporary and can not be accessed again, there is no reason to
provide persistent storage. So we turn it all off - particularly the home directories.

```yaml
# nfs functionality explicitly disabled in case a common.values.yaml
# file is used to enable it for all hubs in the cluster
nfs:
  enabled: false
  pv:
    enabled: false

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

## (Optional) Sharing `shared` directories from another hub with an ephemeral hub

In some specific cases, we may need to share a `shared` directory from another hub
on the same cluster with the ephemeral hub. The 'source' hub whose `shared` directory
we mount may be used to provide common data files, teaching materials, etc for the
ephemeral hub's users.

1. Setup the [PersistentVolume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
   in the ephemeral hub's config to point to the same NFS share that the 'source' hub is
   pointing to, with the following config:

   ```yaml
   # nfs functionality enabled for this ephemeral hub to mount
   # a shared folder from another hub in the cluster
   nfs:
     enabled: true
     dirsizeReporter:
       enabled: false
     pv:
       enabled: true
       mountOptions: <copied-from-source-hub>
       serverIP: <copied-from-source-hub>
       baseShareName: <copied-from-source-hub>
       shareNameOverride: <name-of-source-hub>
   ```

   A few options should copied from the config of the 'source' hub, and `shareNameOverride`
   should be set to whatever is the `name` of the 'source' hub in `cluster.yaml`.

   When deployed, this should set up a new PersistentVolume for the ephemeral hub to use
   that references the same NFS share of the 'source' hub. You can validate this by
   comparing them:

   ```bash
   # Get the source hub's NFS volume
   kubectl get pv <source-hub-name>-home-nfs -o yaml
   # Get the ephemeral hub's NFS volume
   kubectl get pv <ephemeral-hub-name>-home-nfs -o yaml
   ```

   The section under `spec.nfs` should match for both these `PersistentVolume` options.

   ```{note}
   If you want to learn more about how this is setup, look into `helm-charts/basehub/templates/nfs.yaml`
   ```

2. Mount *just* the shared directory appropriately:

   ```yaml
   jupyterhub:
     singleuser:
       storage:
         # We still don't want to have per-user storage
         type: none
         extraVolumes:
           - name: shared-dir-pvc
             persistentVolumeClaim:
               # The name of the PVC setup by nfs.yaml for the ephemeral hub to use
               claimName: home-nfs
         extraVolumeMounts:
           - name: shared-dir-pvc
             mountPath: /home/jovyan/shared
             subPath: _shared
             readOnly: true
   ```

   This will mount the shared directory from the 'source' hub under `shared` in the
   ephemeral hub - so admins can write stuff to the `shared-readwrite` directory in the
   'source' hub and it'll immediately show up here! It's mounted to be read-only - since
   there are no real 'users' in an ephemeral hub, if we make it readwrite, it can be easily
   deleted (accidentally or intentionally) with no accountability.

## Image configuration in chart

The image needs to be specified in the chart directly and not via the JupyterHub
configurator because with `tmpauthenticator` we can't distinguish admin users to
have such rights without providing it to every user.

```yaml
jupyterhub:
  singleuser:
    # image could also be configured via singleuser.profileList configuration
    image:
      name: <image-name>
      tag: <tag>
```

## Enable hook pre-puller & disable JupyterHub

Startup time is very important in ephemeral hubs, and since the JupyterHub
configurator can not be used (no admin users), [the hook pre-puller](https://z2jh.jupyter.org/en/stable/administrator/optimization.html#pulling-images-before-users-arrive)
can be enabled.

```yaml
jupyterhub:
  custom:
    jupyterhubConfigurator:
      enabled: false
  prePuller:
    hook:
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

## Use `nbgitpuller` for distributing content

We encourage users to use [nbgitpuller](https://github.com/jupyterhub/nbgitpuller)
for distributing content. This allows creation of a specific link that will
put users who click it on a specific notebook with a specific UI (such as lab,
classic notebook, RStudio, etc).

The [nbgitpuller link generator](http://nbgitpuller.link/) supports mybinder.org
style links, but for use with *ephemeral hubs*, just use the regular 'JupyterHub'
link generator. [Firefox](https://addons.mozilla.org/en-US/firefox/addon/nbgitpuller-link-generator/)
and [Google Chrome](https://chrome.google.com/webstore/detail/nbgitpuller-link-generato/hpdbdpklpmppnoibabdkkhnfhkkehgnc)
extensions are also available.


## (Optional) Shared systemwide password setup

Optionally, in addition to the cryptnono setup documented above, a shared
password may be used as additional protection to guard against random cryptobros
abusing using our systems for 'free' compute. This password is same for all
users, and can be shared by the community champions of the hub in whatever form
they wish.

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

### Customizing the uptime check to expect a HTTP `401`

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