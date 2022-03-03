# Our CI/CD system

## Overview

We use [GitHub Actions](https://docs.github.com/en/actions) as our CI/CD vendor and all our workflows are defined as YAML files in the [`.github/workflows` folder](https://github.com/2i2c-org/infrastructure/tree/master/.github/workflows) in the `infrastructure` repo.

## Automatic hub deployment

The best place to learn about the latest state of our *automatic* hub deployment
is to look at [the `deploy-hubs.yaml` GitHub Actions workflow file](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-hubs.yaml).
That workflow defines the automatic hub deployment for many of our major clusters.

Currently, our CI/CD system is triggered on pushes to the default branch when any of the
following paths are modified:

```
- deployer/**
- helm-charts/**
- requirements.txt
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

## Helm chart values and cluster config validation

All of our [helm charts](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts) have associated `values.schema.yaml` files and we also maintain a custom [`cluster.schema.yaml` file](https://github.com/2i2c-org/infrastructure/blob/HEAD/shared/deployer/cluster.schema.yaml).
Here is an example of a [`values.schema.yaml` file from the basehub chart](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/basehub/values.schema.yaml).
These schemas explicitly list what values can be passed through our config, and what type these values should have.
Therefore, we can use these schemas to validate all our config before making deploys, and catch bugs early.

We have [functions within the deployer](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/__main__.py#L213-L302) that validate the cluster config, the support chart values, and the helm chart values for each hub against these schemas.
We automatically run these functions in GitHub Actions configured by the [`validate-clusters.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/validate-clusters.yaml).
This workflow is triggered when changes to files along the following filepaths are detected.

```
- config/clusters/**
- deployer/**
- helm-charts/basehub/**
- helm-charts/daskhub/**
- helm-charts/support/**
- requirements.txt
- .github/workflows/validate-hubs.yaml
```
