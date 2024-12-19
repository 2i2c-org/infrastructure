(cicd/hub)=
# Automatic hub deployment

```{admonition} Further reading
You can learn more about this workflow in our blog post [Multiple JupyterHubs, multiple clusters, one repository](https://2i2c.org/blog/2022/ci-cd-improvements/).
```

The best place to learn about the latest state of our *automatic* hub deployment
is to look at [the `deploy-hubs.yaml` GitHub Actions workflow file](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-hubs.yaml).
This workflow file depends on a locally defined action that [sets up access to a given cluster](https://github.com/2i2c-org/infrastructure/blob/main/.github/actions/setup-deploy/action.yaml) and itself contains a range of jobs, the most relevant ones of which are detailed below.
There are also some filtering/optimisation jobs which are not discussed here.

## Main hub deployment workflow

(cicd/hub/generate-jobs)=
### 1. `generate-jobs`: Generate Helm upgrade jobs

The first job takes a list of files that have been added/modified as part of a Pull Request and pipes them into the [`generate-helm-upgrade-jobs` sub-command](https://github.com/2i2c-org/infrastructure/blob/main/deployer/helm_upgrade_decision.py) of the [deployer module](https://github.com/2i2c-org/infrastructure/tree/main/deployer).
This sub-command uses a set of functions to calculate which hubs on which clusters require a helm upgrade, alongside whether the support chart and staging hub(s) on that cluster should also be upgraded.
If any production hubs require an upgrade, the upgrade of the staging hub(s) is a requirement.

This job provides the following outputs:

- Three JSON objects that can be read by later GitHub Actions jobs to define matrix jobs.
  These JSON objects detail: which clusters require their support chart to be upgraded, which staging hub(s) require an upgrade, and which production hubs require an upgrade.
- The above JSON objects are also rendered as human-readable tables using [`rich`](https://github.com/Textualize/rich).

```{admonition} Some special cased filepaths
While the aim of this workflow is to only upgrade the pieces of the infrastructure that require it with every change, some changes do require us to redeploy everything.

- If a cluster's `cluster.yaml` file has been modified, we upgrade the support chart and **all** hubs on **that** cluster. This is because we cannot tell what has been changed without inspecting the diff of the file.
- If any of the `basehub` or `daskhub` Helm charts have additions/modifications in their paths, we redeploy **all** hubs across **all** clusters.
- If the `support` Helm chart has additions/modifications in its path, we redeploy the support chart on **all** clusters.
- If the `deployer` module has additions/modifications in its path, then we redeploy **all** hubs on **all** clusters.
```

### 2. `upgrade-support`: Upgrade support Helm chart on clusters that require it

The next job reads in one of the JSON objects detailed above that defines which clusters need their support chart upgrading.
A matrix job is set up that parallelises over all the clusters defined in the JSON object.
For each cluster, the support chart is upgraded (if required).
We set an output variable from this job to determine if any support chart upgrades fail for a cluster.
We then use these outputs to filter out the failed clusters and prevent further deployments to them, without impairing deployments to unrelated clusters.

### 3. `upgrade-staging`: Upgrade Helm chart for staging hub(s) in parallel

Next we deploy the staging hub(s) on a cluster.
We use staging hubs as [canary deployments](https://sre.google/workbook/canarying-releases/) and prevent deploying production hubs if a staging deployment fails.
Similarly to `upgrade-support`, the last step of this job is to set an output variable that stores if the job completed successfully or failed.

### 4. `upgrade-prod`: Upgrade Helm chart for production hubs in parallel

This last job deploys all production hubs that require it in parallel to the clusters that successfully completed a staging upgrade.

(cicd/hub/pr-comment)=
## Posting the deployment plan as a comment on a Pull Request

The [`generate-jobs`](cicd/hub/generate-jobs) job outputs tables of all the hubs across all the clusters that will be upgraded as a result of changes in the repository.
However, this table can be difficult to track down in amongst the GitHub Actions logs.
Therefore, we have another workflow that will post this information as a comment on the Pull Request that triggered the run for discoverability.

When `generate-jobs` has been triggered by a PR, extra steps are run: first, the [deployer converts the matrix jobs into Markdown tables](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/utils.py#L40-L137) (provided there are valid jobs) and saves them to a file; and second, the job exports the number of the PR to a file.
These files are then uploaded as [GitHub Actions artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts).

Upon the successful completion of the ["Deploy and test hubs" workflow](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/deploy-hubs.yaml), the ["Comment Hub Deployment Plan to a Pull Request" workflow](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/comment-deployment-plan-pr.yaml) is executed.

This workflow downloads the artifacts uploaded by `generate-jobs` and then uses the GitHub API to complete the following tasks:

- Establish whether a deployment plan has already been added to the Pull Request, as identified by a comment made by the user `github-actions[bot]` and the presence of the `<!-- deployment-plan -->` tag in the comment body.
- Either update an existing comment or create a new comment on the PR posting the Markdown tables downloaded as an artifact.

```{admonition} Why we're using artifacts and separate workflow files
Any secrets used by GitHub Actions are not available to Pull Requests that come from forks by default to protect against malicious code being executed with privileged access. `generate-jobs` needs to run in the PR context in order to establish which files are added/modified, but the required secrets would not be available for the rest of the workflow that would post a comment to the PR.

To overcome this in a secure manner, we upload the required information (the body of the comment to be posted and the number of the PR the comment should be posted to) as artifacts.
We then trigger a **new** workflow, **not** running in the PR context and with secret access, to complete the process of interacting with the API to post the comment.

See this blog on [securing workflows](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/) for more context.
```
