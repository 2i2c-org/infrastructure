(cicd)=
# Our CI/CD system

## Overview

We use [GitHub Actions](https://docs.github.com/en/actions) as our CI/CD vendor and all our workflows are defined as YAML files in the [`.github/workflows` folder](https://github.com/2i2c-org/infrastructure/tree/master/.github/workflows) in the `infrastructure` repo.

Longer or more complex workflows are discussed on their own pages (listed in the table of contents), whereas you can find descriptions of simpler or shorter workflows further down this page.

```{toctree}
:maxdepth: 2

hub-deploy.md
auto-bumping.md
```

## Helm chart values and cluster config validation

All of our [helm charts](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts) have associated `values.schema.yaml` files and we also maintain a custom [`cluster.schema.yaml` file](https://github.com/2i2c-org/infrastructure/blob/HEAD/shared/deployer/cluster.schema.yaml).
Here is an example of a [`values.schema.yaml` file from the basehub chart](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/basehub/values.schema.yaml).
These schemas explicitly list what values can be passed through our config, and what type these values should have.
Therefore, we can use these schemas to validate all our config before making deploys, and catch bugs early.

We have [functions within the deployer](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/__main__.py#L213-L302) that validate the cluster config, the support chart values, and the helm chart values for each hub against these schemas.
We automatically run these functions in GitHub Actions configured by the [`validate-clusters.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/validate-clusters.yaml).
This workflow is only triggered when related configuration has changed.

## Finding the right workflow runs

GitHub's UI is slightly confusing for distinguishing between _workflows that ran on a Pull Request_ and _workflows that ran on the merge commit to the default branch_.

To help contributors to our `infrastructure` repository find the right workflow run, we have a GitHub Actions workflow that [posts a comment on a just merged Pull Request](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/comment-test-link-merged-pr.yaml) with a link to the GitHub Actions run of the `deploy-hubs.yaml` workflow (described in [](cicd/hub)) that the merge triggered.
Hence, it should be much easier to find the current deployments caused by merges than just following GitHub's UI.
