(hub-deployment-guide:runbooks:phase3)=
# Phase 3: Hub setup

This assumes a cluster where the hub will be deployed to already exists

## Phase 3.1: Initial setup

### Definition of ready

The following lists the information that needs to be available to the engineer before this phase can start.

- Name of the hub
- Dask gateway?
- Splash image
- URL of the community's webpage
- Funded_by information (name and URL)
- Authentication Mechanism
- Admin Users

### Outputs

At the end of Phase 3.1 both 2i2c engineers and the admin users mentioned can login to the hub.

The file assets that should have been generated and included in the PR should be:

```bash
➕ config/clusters/<new-cluster-name>
  ├── common.values.yaml
  ├── <new-hub-name>.values.yaml
  └── enc-<new-hub-name>.secret.values.yaml
```

```{tip}
When reviewing cluster setup PRs, make sure the files above are all present.
```

### Initial setup runbook

All of the following steps must be followed in order to consider phase 3.1 complete. Steps might contain references to other smaller, topic-specifc runbooks that are gathered together and listed in the order they should be carried on by an engineer.

1. Determine the **hub helm chart** that is needed.

   Use the info provided in the new hub GitHub issue for the `Dask gateway` section.
   If Dask gateway will be needed, then go for a `daskhub` helm chart, otherwise choose a `basehub`.

   Store the helm type under $HELM_CHART_TYPE env var:

   ```bash
   export $HELM_CHART_TYPE=type
   ```

   For more information about our hub helm charts and how to choose, see [](hub-helm-charts).

   ```{seealso}
   See [](/topic/infrastructure/config.md) for general information about hub helm chart configuration.
   ```

2. Determine the address of the file storage server that a hub on this cluster should use for connecting to it.

    `````{tab-set}
    ````{tab-item} AWS
    :sync: aws-key
    Get the address of the EFS server via terraform and store it as it will be required in a later step.

    ```bash
    terraform output nfs_server_dns
    ```
    ````

    ````{tab-item} Google Cloud
    :sync: gcp-key
    Get the address of the Google FileStore IP from the UI and store it as it will be required in a later step.
    ````

    ````{tab-item} Azure
    :sync: azure-key
    N/A
    ````
    `````

3. Create the relevant values.yaml file/s under the appropriate cluster directory.

   If the cluster will have multiple hubs, and chances are it will as there's a common 2i2c practice to always deploy a staging hub alongside a production one, then create two values.yaml files under the appropriate cluster directory.

   One file will hold the common hubs configuration and one will hold the specific hub configuration.

   ```bash
   export $CLUSTER_NAME=cluster-name;
   export $HUB_NAME=hub-name
   ```

   Make sure you are in the root of the infrastructure repository and run:

   ```bash
   touch ./config/clusters/$CLUSTER_NAME/$HUB_NAME.values.yaml;
   touch ./config/clusters/$CLUSTER_NAME/common.values.yaml
   ```

4. Run the deployer to configure the hub using the information available in this phase.

   The easiest way to add new configuration is to use the deployer to generate an initial config.

   You will be asked to input all the information needed for the commands to run successfully. Follow the instructions and using the information provided to you, fill in all the information.

   Run the deployer commands below to generate config for the specific hub configuration:
   ```bash
   deployer generate hub-asset main-values-file
   ```

   Run the deployer commands below to generate config for the common hubs configuration:
   ```bash
   deployer generate hub-asset main-values-file
   ```

   ```{tip}
   Each `*.values.yaml` file is a Zero to JupyterHub configuration, and you can customize whatever you like.
   ```

4. Setup the relevant Authentication Provider with relevant credentials.
   See [](enable-auth-provider) for steps on how to achieve this.

5. Then reference these files in a new entry under the `hubs` key in the cluster's `cluster.yaml` file.

   You can use the `deployer generate hub-asset` subcommand to generate the relevant entry to insert into cluster.yaml file.

   ```bash
   deployer generate hub-asset cluster-entry --cluster-name $CLUSTER_NAME --hub-name $HUB_NAME --hub-type $HELM_CHART_TYPE
   ```

   ```{warning}
   Please pay attention to all the fields that have been auto-generated for you by this command and change every one that doesn't match the community's requirements or was not rendered correctly before copying-pasting it into the relevant files.
   ```

6. Create a Pull Request with the new hub entry, and get a team member to review it.
7. Once you merge the pull request, the GitHub Action workflow will detect that a new entry has been added to the configuration file.
   It will then deploy a new JupyterHub with the configuration you've specified onto the corresponding cluster.
8. Once you merge the pull request, the GitHub Action workflow will detect that a new entry has been added to the configuration file.
   It will then deploy a new JupyterHub with the configuration you've specified onto the corresponding cluster.
9. Monitor the action to make sure that it completes.
   If something goes wrong and the workflow does not finish, try [deploying locally](hubs:manual-deploy) to access the logs to help understand what is going on.
   It may be necessary to make new changes to the hub's configuration via a Pull Request, or to *revert* the old Pull Request if you cannot determine how to resolve the problem.

   ```{attention}
   In order to protect sensitive tokens, our CI/CD pipeline will **not** print testing output to its logs.
   You will need to run the [health check locally](hubs:manual-deploy:health-check) to inspect these logs.
   ```

10. Log in to the hub and ensure that the hub works as expected from a user's perspective.
11. Send a link to the hub's Community Representative(s) so they can confirm that it works from their perspective as well.