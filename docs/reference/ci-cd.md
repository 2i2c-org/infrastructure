(cicd)=
# Our CI/CD system

## Overview

We use [GitHub Actions](https://docs.github.com/en/actions) as our CI/CD vendor and all our workflows are defined as YAML files in the [`.github/workflows` folder](https://github.com/2i2c-org/infrastructure/tree/master/.github/workflows) in the `infrastructure` repo.

(cicd/hub)=
## Automatic hub deployment

```{admonition} Further reading
You can learn more about this workflow in our blog post [Multiple JupyterHubs, multiple clusters, one repository](https://2i2c.org/blog/2022/ci-cd-improvements/).
```

The best place to learn about the latest state of our *automatic* hub deployment
is to look at [the `deploy-hubs.yaml` GitHub Actions workflow file](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-hubs.yaml).
This workflow file depends on a locally defined action that [sets up access to a given cluster](https://github.com/2i2c-org/infrastructure/blob/master/.github/actions/setup-deploy/action.yaml) and itself contains four main jobs, detailed below.

(cicd/hub/generate-jobs)=
### 1. `generate-jobs`: Generate Helm upgrade jobs

The first job takes a list of files that have been added/modified as part of a Pull Request and pipes them into the [`generate-helm-upgrade-jobs` sub-command](https://github.com/2i2c-org/infrastructure/blob/master/deployer/helm_upgrade_decision.py) of the [deployer module](https://github.com/2i2c-org/infrastructure/tree/master/deployer).
This sub-command uses a set of functions to calculate which hubs on which clusters require a helm upgrade, alongside whether the support chart and staging hub on that cluster should also be upgraded.
If any production hubs require an upgrade, the upgrade of the staging hub is a requirement.

This job provides the following outputs:

- Two JSON objects that can be read by later GitHub Actions jobs to define matrix jobs.
  These JSON objects detail: which clusters require their support chart and/or staging hub to be upgraded, and which production hubs require an upgrade.
- The above JSON objects are also rendered as human-readable tables using [`rich`](https://github.com/Textualize/rich).

#### Some special cased filepaths

While the aim of this workflow is to only upgrade the pieces of the infrastructure that require it with every change, some changes do require us to redeploy everything.

- If a cluster's `cluster.yaml` file has been modified, we upgrade the support chart and **all** hubs on **that** cluster. This is because we cannot tell what has been changed without inspecting the diff of the file.
- If either the `basehub` or `daskhub` Helm charts have additions/modifications in their paths, we redeploy **all** hubs across **all** clusters.
- If the support Helm chart has additions/modifications in its path, we redeploy the support chart on **all** clusters.
- If the deployer module has additions/modifications in its path, then we redeploy **all** hubs on **all** clusters.

```{note}
Right now, we redeploy everything when the deployer changes since the deployer undertakes some tasks that generates config related to authentication.
This may change in the future as we move towards the deployer becoming a separable, stand-alone package.
```

### 2. `upgrade-support-and-staging`: Upgrade support and staging hub Helm charts on clusters that require it

The next job reads in one of the JSON objects detailed above that defines which clusters need their support chart and/or staging hub upgrading.
*Note that it is not a requirement for both the support chart and staging hub to be upgraded during this job.*
A matrix job is set up that parallelises over all the clusters defined in the JSON object.
For each cluster, the support chart is first upgraded (if required) followed by the staging hub (if required).

```{note}
The 2i2c cluster is a special case here as it has two staging hubs: one running the `basehub` Helm chart, and the other running the `daskhub` Helm chart.
We therefore run an extra step for the 2i2c cluster to upgrade the `dask-staging` hub (if required).
```

We use staging hubs as [canary deployments](https://sre.google/workbook/canarying-releases/) and prevent deploying production hubs if a staging deployment fails.
Hence, the last step of this job is to set an output variable that stores if the job completed successfully or failed.

### 3. `filter-generate-jobs`: Filter out jobs for clusters whose support/staging job failed

This job is an optimisation job.
While we do want to prevent all production hubs on Cluster X from being upgraded if its support/staging job fails, we **don't** want to prevent the production hubs on Cluster Y from being upgraded because the support/staging job for Cluster X failed.

This job reads in the production hub job definitions generated in job 1 and the support/staging success/failure variables set in job 2, then proceeds to filter out the productions hub upgrade jobs that were due to be run on a cluster whose support/staging job failed.

### 4. `upgrade-prod-hubs`: Upgrade Helm chart for production hubs in parallel

This last job deploys all production hubs that require it in parallel to the clusters that successfully completed job 2.

### Known issues with this workflow

Sometimes the [`generate-jobs` job](cicd/hub/generate-jobs) fails with the following message:

```
The head commit for this pull_request event is not ahead of the base commit. Please submit an issue on this action's GitHub repo.
```

This issue is [tracked upstream](https://github.com/jitterbit/get-changed-files/issues/11) and can be resolved by rebasing your branch against `master`.

## Helm chart values and cluster config validation

All of our [helm charts](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts) have associated `values.schema.yaml` files and we also maintain a custom [`cluster.schema.yaml` file](https://github.com/2i2c-org/infrastructure/blob/HEAD/shared/deployer/cluster.schema.yaml).
Here is an example of a [`values.schema.yaml` file from the basehub chart](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/basehub/values.schema.yaml).
These schemas explicitly list what values can be passed through our config, and what type these values should have.
Therefore, we can use these schemas to validate all our config before making deploys, and catch bugs early.

We have [functions within the deployer](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/__main__.py#L213-L302) that validate the cluster config, the support chart values, and the helm chart values for each hub against these schemas.
We automatically run these functions in GitHub Actions configured by the [`validate-clusters.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/validate-clusters.yaml).
This workflow is only triggered when related configuration has changed.
