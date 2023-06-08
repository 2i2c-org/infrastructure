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

## Required workflows and author auto-assignment

To make the most out of the [Project Boards](https://github.com/orgs/2i2c-org/projects) that 2i2c uses, the [`auto-author-assign-pull-request.yaml`](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/auto-author-assign-pull-request.yaml) workflow automatically assigns authors to Pull Requests.

Because this is a practice that we wish to have across other 2i2c repositories, an equivalent of the `auto-author-assign-pull-request.yaml` workflow in https://github.com/2i2c-org/infrastructure exists in https://github.com/2i2c-org/.github/tree/HEAD/workflows. The workflow in the https://github.com/2i2c-org/.github repository is marked as a [required workflow](https://docs.github.com/en/actions/using-workflows/required-workflows). This means that it will run on every PR in the repositories that it's setup as required for.

```{note}
An additional, slightly different workflow than the one in https://github.com/2i2c-org/infrastructure is set up in the https://github.com/2i2c-org/.github repository
because we want to avoid adding up to [GitHub's API rate limits](https://docs.github.com/en/rest/rate-limit) for https://github.com/2i2c-org/infrastructure.

Hence, the workflow in https://github.com/2i2c-org/infrastructure, will only trigger when PRs are opened/reopened instead of every time they are updated.

This is because a _GitHub Required Workflow_ is expected to successfully run **for each commit** in that Pull Request, otherwise merging it will be **blocked**.
```
