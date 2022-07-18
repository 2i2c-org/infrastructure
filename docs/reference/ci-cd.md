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

### Posting the deployment plan as a comment on a Pull Request

The [`generate-jobs`](cicd/hub/generate-jobs) job outputs tables of all the hubs across all the clusters that will be upgraded as a result of changes in the repository.
However, this table can be difficult to track down in amongst the GitHub Actions logs.
Therefore, we have another workflow that will post this information as a comment on the Pull Request that triggered the run for discoverability.

When `generate-jobs` has been triggered by a PR, extra steps are run: first, the deployer converts the matrix jobs into Markdown tables (provided there are valid jobs) and saves them to a file; and second, the job exports the number of the PR to a file.
These files are then uploaded as [GitHub Actions artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts).

Upon completion of the ["Deploy and test hubs" workflow](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/deploy-hubs.yaml), the ["Comment Hub Deployment Plan to a Pull Request" workflow](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/comment-deployment-plan-pr.yaml) is executed.

This workflow downloads the artifacts uploaded by `generate-jobs` and then uses the GitHub API to complete the following tasks:

- Establish whether a deployment plan has already been added to the Pull Request, as identified by a comment made by the user `github-actions[bot]` and the presence of the `<!-- deployment-plan -->` tag in the comment body.
- Either update an existing comment or create a new comment on the PR posting the Markdown tables downloaded as an artifact.

```{admonition} Why we're using artifacts and separate workflow files

Any secrets used by GitHub Actions are not available to Pull Requests that come from forks by default to protect against malicious code being executed with privileged access. `generate-jobs` needs to run in the PR context in order to establish which files are added/modified, but the required secrets would not be available for the rest of the workflow that would post a comment to the PR.

To overcome this in a secure manner, we upload the required information (the body of the comment to be posted and the number of the PR the comment should be posted to) as artifacts.
We then trigger a **new** workflow, **not** running in the PR context and with secret access, to complete the process of interacting with the API to post the comment.

See this blog on [securing workflows](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/) for more context.
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

To help contributors to our `infrastructure` repository find the right workflow run, we have a GitHub Actions workflow that [posts a comment on a just merged Pull Request](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/comment-test-link-merged-pr.yaml) with a link to the GitHub Actions UI filtered for the `deploy-hubs.yaml` workflow (described above) running on the default branch.
Hence, it should be much easier to find the current deployments happening on `master` than just following GitHub's UI.

## Automatically bumping image tags and helm sub-chart versions

Throughout the `infrastructure` repo we have a few upstream dependencies.
This section will focus on the images our JupyterHubs use to define environments and services, the sub-charts our helm charts are built on top of, and the process we have for automatically keeping these up-to-date with upstream releases.

### Bumping image tags

To keep the tags of any images we use up-to-date with upstream container registries, we use this Action: [sgibson91/bump-jhub-image-action](https://github.com/sgibson91/bump-jhub-image-action) in the [`bump-image-tags.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/bump-image-tags.yaml).

This workflow runs as a matrix where one matrix job relates to one config file.
A config file might be a `*.values.yaml` file for a specific hub, or a `values.yaml` file for a helm chart.
But all it really needs to contain is valid YAML!

Two inputs are required for this Action:

1. The path to the config file as defined from the root of the repository, e.g., `helm-charts/basehub/values.yaml`
2. A variable called `images_info` which is a list of dictionaries containing information about the images we wish to bump in the given config file.
   By providing a list in this way, we can choose to include/exclude images in the given config from being bumped.

Each dictionary in the `images_info` list must have a `values_path` key whose value is a valid [JMESPath expression](https://jmespath.org) to the image we would like to bump.
The example below would bump the `singleuser` image.

```json
[{"values_path": ".singleuser.image"}]
```

Additionally, you can provide a `regexpr` key with a valid regular expression that will filter the tags available on the container registry.
This can be particularly useful if the image has different tags published, e.g., commit tags as well as date tags, etc.

```{admonition} More configuration options
Please see the [project README](https://github.com/sgibson91/bump-helm-deps-action#readme) for more information about configuring this Action.
```

When triggered, either on a schedule or by a workflow dispatch event, the Action will open a Pull Request for each item in the matrix, bumping the tags for the defined images in the defined config for each matrix job.

```{warning}
Currently this Action only works for images that are **publicly available** on either **Docker Hub** or **quay.io**.

- To contribute support for other container registries, see [this issue](https://github.com/sgibson91/bump-jhub-image-action/issues/73)
- To contribute support for authenticated calls to container registries, see [this issue](https://github.com/sgibson91/bump-jhub-image-action/issues/99)
```

### Bumping helm sub-chart versions

To keep the versions of sub-charts (charts our helm charts depend on) up-to-date with upstream releases, we use this Action: [sgibson91/bump-helm-deps-action](https://github.com/sgibson91/bump-helm-deps-action) in the [`bump-helm-versions.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/bump-helm-versions.yaml).

This workflow runs as a matrix where one matrix job relates to one of our helm charts, e.g., `basehub`.
A config file is where the dependencies for that helm chart are listed.
This is usually in a `Chart.yaml` file, but has historically also been a `requirements.yaml file`.
All it really needs to contain is valid YAML!

Two inputs are required for this Action:

1. The path to the config file as defined from the root of the repository, e.g., `helm-charts/basehub/Chart.yaml`
2. A variable called `chart_urls` which is a dictionary containing information about the sub-charts we wish to bump in the given config file.
   By providing a dictionary in this way, we can choose to include/exclude sub-charts in the given config from being bumped.

The `chart_urls` has the sub-charts we wish to bump as keys, and URLs where a list of pulished versions of those charts is available.
An example below would bump the JupyterHub subchart of the basehub helm chart.

```json
{"jupyterhub": "https://jupyterhub.github.io/helm-chart/index.yaml"}
```

Note that the URL is not the expected <https://jupyterhub.github.io/helm-chart/>.
This is so the Action can pass the file contents directly to a YAML parser, rather than having to scrape the rendered site's HTML.

```{admonition} More configuration options
Please see the [project README](https://github.com/sgibson91/bump-jhub-image-action#readme) for more information about configuring this Action.
```

When triggered, either on a schedule or by a workflow dispatch event, the Action will open a Pull Request for each item in the matrix, bumping the versions for the defined sub-charts in the defined config for each matrix job.

```{warning}
Currently this Action only works for sub-charts that have a YAML formatted index of versions published at a URL that either:

- contains `/gh-pages/`, or;
- ends with `index.yaml` (or `index.yml`).

Other sources for version lists, such as GitHub Releases or HTML sites, will need to have code added upstream as they are required.
```
