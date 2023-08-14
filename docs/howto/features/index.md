(hub-features)=
# Enable specific hub features

There are several extra features and services that can be enabled on the 2i2c JupyterHubs.
These add extra functionality, connect with cloud services, etc.
See the sections below for more details.

## Layers

### Cloud
1. Shared/Dedicated Cluster
2. Dedicated nodepool on a shared cluster (recommended for events)

### Hub User Access
1. Authentication + authorization
2. Anonymisation of users ids

### Community customizations
1. Community specific hub domain
2. (mandatory) Hub login page template sections
3. Self-configuration of hub login page from own GitHub repository
4. Customizations of hub pages

### Data
1. Shared data directories
2. Object storage buckets (persistent/scratch)
  - Cloud Permissions
    - (default) Buckets accessible from the Hub
    - Buckets accessible from outside the Hub
      - Publicly accessible
      - (GCP only) Google groups based membership
    - (GCP only) Requestor pays for buckets

### Integrations

1. Allow users to push to GitHub from the Hub (gh-scoped-creds)
2. Enable `nbgitpuller` for private repos (git-credential-helper)
3. (dedicated clusters only) Grafana
4. Authenticated static websites
5. (default enabled) Configurator

### Performance

1. GPUs
  - GPU user profile
2. Dask
3. KernelCulling

### Elastic Scaffolding

1. ProfileLists
  - Hardware Profiles
  - User Image Selectors
  - Node Sharing

### Knowledge sharing
### Support and training

```{toctree}
:maxdepth: 2
:caption: Access
cloud-access.md
gpu.md
github.md
anonymized-usernames.md
private-nbgitpuller.md
```

```{toctree}
:maxdepth: 2
:caption: Configuring pages
login-page.md
static-sites.md
```

```{toctree}
:maxdepth: 2
:caption: Storage
buckets.md
per-user-db.md
shared-db.md
```

```{toctree}
:maxdepth: 2
:caption: User image
image.md
rocker.md
```

```{toctree}
:maxdepth: 2
:caption: Hub Types
ephemeral.md
```

```{toctree}
:maxdepth: 2
:caption: Other
dedicated-nodepool.md
allow-unlisted-profile-choice.md
```
