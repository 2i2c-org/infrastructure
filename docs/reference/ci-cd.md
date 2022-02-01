# Our CI/CD system

The best place to learn about the latest state of our *automatic* hub deployment
is to look at [the `deploy-hubs.yaml` GitHub workflow](https://github.com/2i2c-org/pilot-hubs/tree/HEAD/.github/workflows/deploy-hubs.yaml).
That workflow defines the automatic hub deployment for many of our major clusters.

Currently, our CI/CD system is triggered on pushes to the default branch when any of the
following paths are modified:

```
- deployer/**
- helm-charts/**
- requirements.txt
- dev-requirements.txt
- config/secrets.yaml
- config/clusters/**
- .github/workflows/deploy-hubs.yaml
- .github/actions/deploy/**
```

The deployment matrix includes our existing clusters with references to the corresponding
cloud provider so we can effectively run cluster specifics steps depending on where the
cluster is deployed.

The following steps are path-filtered so we can trigger new deployments on specific
clusters when the associated files are actually changed.

Finally, the [deploy action](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/actions/deploy/action.yml)
is called which in turn will use the deployer script to deploy the hubs on the corresponding
clusters.

:::{note}
TODO: This is yet small, it needs to be extended to talk more about our CI/CD system.
:::
