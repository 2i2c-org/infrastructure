(sre-guide:support-chart-upgrades)=
# How to upgrade the versions of the support chart's dependencies

The support chart depends on some external helm charts which have their own release cadence.
We also have an extra dependency in `cert-manager` managed by the `deployer`.
This documentation covers the steps to take to update the version of these dependencies and rolling them out.

## Runbook steps

1. *Trigger the [GitHub Action workflow] to generate a PR that will bump the versions of the support chart's dependencies if newer versions are available.*

1. *Check for a new `cert-manager` release and bump the value in the `deployer`.*

   `cert-manager` is not listed as a dependency of the support chart since it is deployed into it's own namespace.
   Instead the code that handles installing it lives in the deployer.

   You can find the latest available of `cert-manager` by checking the [releases page] or by running the below command in a terminal.

   ```bash
   helm search repo jetstack/cert-manager --versions
   ```

    Update the [section of `deployer` code] that installs `cert-manager` with the new version, and commit this to the same PR that the workflow opened.
    You can get a copy of the PR locally by running this [`gh`] command:

    ```bash
    gh pr checkout <pr-number>
    ```

1. *For any dependencies that will be bumped, check the release notes for mention of any breaking changes we should be aware of.*
   
   If you find a breaking change or are unsure of a specific upgrade, you can revert the change in the PR, commit and push it.

1. *Deploy the PR to a test cluster and monitor it.*

   Choose a test cluster to deploy the PR to and monitor it for 24 hours or so.
   If the `cluster-autoscaler` dependency is being upgraded, then it's best to test on an AWS cluster as that dependency is only enabled on AWS deployment.

   ```bash
   deployer deploy-support $CLUSTER_NAME
   ```

1. *If there are no issues with the test cluster, merge the PR to deploy to all clusters.*

[GitHub Action workflow]: https://github.com/2i2c-org/infrastructure/actions/workflows/bump-helm-versions.yaml
[releases page]: https://cert-manager.io/docs/releases/
[section of deployer code]: https://github.com/2i2c-org/infrastructure/blob/fd17869b88d3dcb55ad87f59f00deca80209ea2d/deployer/commands/deployer.py#L74-L76
[`gh`]: https://github.com/cli/cli#installation
