(hub-features)=
# Enable specific hub features

There are several extra features and services that can be enabled on the 2i2c JupyterHubs.
These add extra functionality, connect with cloud services, etc.
See the sections below for more details.

## Layers

### Cloud Layer
```{toctree}
:maxdepth: 1
1.1. New Kubernetes cluster on GCP or Azure <../../hub-deployment-guide/new-cluster/new-cluster>
1.2. New Kubernetes cluster on AWS <../../hub-deployment-guide/new-cluster/aws>
2. Dedicated nodepool on a shared cluster (recommended for events) <dedicated-nodepool.md>
```

### Access Layer
```{toctree}
:maxdepth: 1
1.1. Authenticate using CILogonOAuthenticator <../../hub-deployment-guide/configure-auth/cilogon>
1.2. Authenticate using GitHubOAuthenticator <../../hub-deployment-guide/configure-auth/github-orgs>
1.3. Authenticate using TmpAuthenticator for an Ephemeral hub <ephemeral.md>
2. Anonymize usernames <anonymized-usernames.md>
```

### Community Customization Layer
```{toctree}
:maxdepth: 1
1. Community specific hub domain <../manage-domains/set-cnames>
2. Configure the hub login page <login-page.md>
```
3. Customizations of hub pages

### Data Layer

```{toctree}
:maxdepth: 1
1. Shared data directories <../../topic/infrastructure/storage-layer>
2. Object storage buckets (persistent/scratch) <buckets.md>
2.1. Cloud Permissions <cloud-access.md>
3. Setup a database server per user <per-user-db.md>
4. Setup a shared database for all users on the hub <shared-db.md>
```

### Integrations Layer

```{toctree}
:maxdepth: 1
1. Allow users to push to GitHub from the Hub (gh-scoped-creds) <github.md>
2. Enable `nbgitpuller` for private repos (git-credential-helper) <private-nbgitpuller.md>
3. Authenticated static websites <static-sites.md>
4. (default enabled) Configurator <https://docs.2i2c.org/admin/howto/configurator>
5. (dedicated clusters only) Grafana <../..//topic/monitoring-alerting/grafana>
6. Provide credentials for using the JupyterHub as an auth provider <auth-provider.md>
```

### Performance Layer
```{toctree}
:maxdepth: 1
1. GPU <gpu.md>
2. Cull resources (jupyterhub-idle-culler) <../../sre-guide/manage-k8s/culling>
```
3. Dask

### Elastic scaffolding Layer
1. ProfileLists
  - Hardware Profiles
  - User Image Selectors
  - Node Sharing

```{toctree}
:maxdepth: 1
2. Allow users to setup custom, free-form user profile choices <allow-unlisted-profile-choice.md>
```

### User image

```{toctree}
:maxdepth: 1
image.md
rocker.md
```

### Other possible layers, but not stabilized yet
  - Knowledge sharing Layer
  - Support Layer
  - Applications Layer
