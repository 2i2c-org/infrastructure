(hub-features)=
# Enable specific hub features

There are several extra features and services that can be enabled on the 2i2c JupyterHubs.
These add extra functionality, connect with cloud services, etc.
See the sections below for more details.

## Layers

### Cloud Layer
1. Shared/Dedicated Cluster

```{toctree}
:maxdepth: 2
2. Dedicated nodepool on a shared cluster (recommended for events) <dedicated-nodepool.md>
```

### Access Layer
1. Authentication + authorization

```{toctree}
:maxdepth: 2
1.1. Ephemeral hub and TmpAuthenticator <ephemeral.md>
2. Anonymized username <anonymized-usernames.md>
```

### Community Customization Layer
1. Community specific hub domain
2. (mandatory) Hub login page template sections

```{toctree}
:maxdepth: 2
3. Self-configuration of hub login page from own GitHub repository <login-page.md>
```
4. Customizations of hub pages

### Data Layer
1. Shared data directories

```{toctree}
:maxdepth: 2
2. Object storage buckets (persistent/scratch) <buckets.md>
2.1. Cloud Permissions <cloud-access.md>
3. Setup a database server per user <per-user-db.md>
4. Setup a shared database for all users on the hub <shared-db.md>
```

### Integrations Layer

```{toctree}
:maxdepth: 2
1. Allow users to push to GitHub from the Hub (gh-scoped-creds) <github.md>
2. Enable `nbgitpuller` for private repos (git-credential-helper) <private-nbgitpuller.md>
3. Authenticated static websites <static-sites.md>
```
4. (default enabled) Configurator
5. (dedicated clusters only) Grafana

### Performance Layer
```{toctree}
:maxdepth: 2
1. GPU <gpu.md>
```
2. Dask
3. Cull resources (jupyterhub-idle-culler)

### Elastic scaffolding Layer
1. ProfileLists
  - Hardware Profiles
  - User Image Selectors
  - Node Sharing

```{toctree}
:maxdepth: 2
2. Allow users to setup custom, free-form user profile choices <allow-unlisted-profile-choice.md>
```

### User image

```{toctree}
:maxdepth: 2
image.md
rocker.md
```

### Other possible layers, but not stabilized yet
  - Knowledge sharing Layer
  - Support Layer
  - Applications Layer