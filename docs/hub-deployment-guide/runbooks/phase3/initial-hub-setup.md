(hub-deployment-guide:runbooks:phase3.1)=
# Phase 3.1: Initial setup

This phase is about a fast initial hub setup that later could be fine-tuned.

## Definition of ready

The following lists the information that needs to be available to the engineer before this phase can start.

- Name of the hub
- Will Dask gateway be required?
- Splash image
- URL of the community's webpage
- Funded by information (name and URL)
- Authentication mechanism
- List of admin users

## Outputs

At the end of Phase 3.1 both 2i2c engineers and the other admin users can login into the hub.

The file assets that should have been generated and included in the PR should be:

```bash
➕ config/clusters/<new-cluster-name>
  ├── common.values.yaml
  ├── <new-hub-name>.values.yaml
  └── enc-<new-hub-name>.secret.values.yaml
```

And the following existing file should have been updated if the new hub was the first in a cluster:

```bash
～ .github/workflows
  └── deploy-hubs.yaml
```

```{tip}
When reviewing initial hub setup PRs, make sure the files above are all present.
```

## Initial setup runbook

All of the following steps must be followed in order to consider phase 3.1 complete. Steps might contain references to other smaller, topic-specific runbooks that are gathered together and listed in the order they should be carried out in by an engineer.


1. **Create the relevant `values.yaml` file/s under the appropriate cluster directory**

    ```bash
      export CLUSTER_NAME=cluster-name;
      export HUB_NAME=hub-name
      ```

   1. **If you're adding a hub to an existing cluster with hubs on it**
      then create only one file to hold the specific hub configuration via

      ```bash
      touch ./config/clusters/$CLUSTER_NAME/$HUB_NAME.values.yaml
      ```

   1. **If the cluster has currently no hubs**

      but will have more than one (and chances are it will as this is a common 2i2c practice to always deploy a staging hub alongside a production one), then create two values.yaml files under the appropriate cluster directory.

      - One file will hold the common hubs configuration and one will hold the specific hub configuration.

      - Make sure you are in the root of the infrastructure repository and run:

      ```bash
      touch ./config/clusters/$CLUSTER_NAME/$HUB_NAME.values.yaml;
      touch ./config/clusters/$CLUSTER_NAME/common.values.yaml
      ```

1. **Run the deployer to generate a sample basic hub configuration**

   The easiest way to add new configuration is to use the deployer to generate an initial sample config.

   You will be asked to input all the information needed for the command to run successfully. Follow the instructions on the screen and using the information provided to you, fill in all the fields.

   ````{important}
   If you are deploying a cluster using openstack, then you need to manually add specific node selectors and disable the z2jh default ones. This is because the magnum CAPI driver that is used by Jetstream2, does not currently support setting custom node selectors on nodepools.

   Example:
   ```yaml
   jupyterhub:
      scheduling:
         corePods:
            nodeAffinity:
            matchNodePurpose: ignore
         userPods:
            nodeAffinity:
            matchNodePurpose: ignore
         userScheduler:
            nodeSelector:
            capi.stackhpc.com/node-group: core
      singleuser:
         nodeSelector:
            capi.stackhpc.com/node-group: user-m3-medium
      proxy:
         chp:
            nodeSelector:
            capi.stackhpc.com/node-group: core
         traefik:
            nodeSelector:
            capi.stackhpc.com/node-group: core
      prePuller:
         hook:
            nodeSelector:
            capi.stackhpc.com/node-group: user-m3-medium
      hub:
         nodeSelector:
            capi.stackhpc.com/node-group: core
   binderhub-service:
      nodeSelector:
         capi.stackhpc.com/node-group: core
         hub.jupyter.org/node-purpose: null
      dockerApi:
         nodeSelector:
            hub.jupyter.org/node-purpose: null
            capi.stackhpc.com/node-group: user-m3-medium
      config:
         KubernetesBuildExecutor:
            node_selector:
               # Schedule builder pods to run on user nodes only
               hub.jupyter.org/node-purpose: null
               capi.stackhpc.com/node-group: user-m3-medium
   ```
   ````

   1. **If you're adding a hub to an existing cluster with hubs on it**

      Then run the deployer command below to generate config for the specific hub configuration:

         - **If this will be a regular JupyterHub then:**

            - **Run:**
               ```bash
               deployer generate hub-asset main-values-file
               ```
            - **Setup the relevant Authentication Provider with relevant credentials**

               See [](enable-auth-provider) for steps on how to achieve this.

         - **If this will be a binderhub style hub, then run:**
            ```bash
            deployer generate hub-asset binderhub-ui-values-file
            ```

            And continue following the guide at [](features:binderhub-ui-hub).

   1. **If the cluster has currently no hubs**

      1. **Determine the address of the storage server that a hub on this cluster should use to connect to it**

          `````{tab-set}
          ````{tab-item} AWS
          :sync: aws-key
          Get the address of the storage via terraform and store it as it will be required in a later step.

          Make sure you are in the right terraform directory, i.e. `terraform/projects/aws` and the right terraform workspace by running `terraform workspace show`.

          For persistent disks, run:

          ```bash
          terraform output ebs_volume_id_map
          ```

          For EFS instances, run:

          ```bash
          terraform output nfs_server_dns_map
          ```
          ````

          ````{tab-item} Google Cloud
          :sync: gcp-key
          Get the address of the storage via terraform and store it as it will be required in a later step.

          Make sure you are in the right terraform directory, i.e. `terraform/projects/aws` and the right terraform workspace by running `terraform workspace show`.

          For persistent disks, run:

          ```bash
          terraform output persistent_disk_id_map
          ```
          
          For Google FileStore instances, get the IP address from the GCP UI.
          ````

          ````{tab-item} Azure
          :sync: azure-key
          tf output azure_fileshare_url
          ````
          `````
      1. **Run the deployer command below to generate config for the common hubs configuration, passing the admin users one by one:**
          ```bash
          deployer generate hub-asset common-values-file --admin-users admin1 --admin-users admin2
          ```

      ```{warning}
      If the admin users list is not passed independently as arguments and is instead left to be passed via de prompt with all the other args, then the following error is raised no matter the value passed: `Error: Value must be an iterable.`.
      ```

   ```{tip}
   Each `*.values.yaml` file is a Helm chart configuration file (`basehub`, or `daskhub`), and you can also configure their chart dependencies (`jupyterhub`, `dask-gateway`, etc).

   You can also look at the entries for similar hubs under the same cluster folder, copy / paste one of them, and make modifications as needed for this specific hub.
   For example, see the hubs configuration in [the 2i2c Google Cloud cluster configuration directory](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/2i2c).
   ```


1. **Then reference these files in a new entry under the `hubs` key in the cluster's `cluster.yaml` file**

   You can use the `deployer generate hub-asset` subcommand to generate the relevant entry to insert into cluster.yaml file.

   ```bash
   deployer generate hub-asset cluster-entry --cluster-name $CLUSTER_NAME --hub-name $HUB_NAME
   ```

   ```{warning}
   Please pay attention to all the fields that have been auto-generated for you by this command and change every one that doesn't match the community's requirements or was not rendered correctly before copying-pasting it into the relevant files.
   ```

   ```{important}
   If you are deploying a binderhub ui style hub, then make sure that in the `cluster.yaml` file **the hub's domain** is entered instead of the binderhub's, for testing purposes.
   ```

1. **Enable dask-gateway**

   Use the info provided in the new hub GitHub issue for the `Dask gateway` section.
   If Dask gateway will be needed, then choose a `basehub`, and follow the guide on
   [how to enable dask-gateway on an existing hub](howto:features:daskhub).

1. **Add the new cluster and staging hub to CI/CD**

   ```{important}
   This step is only applicable if the hub is the first hub being deployed to a cluster **or** has `staging` in it's name.
   ```

   To ensure the new cluster and its hubs are appropriately handled by our CI/CD system, please add it as an entry in the following places in the [`deploy-hubs.yaml`](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/deploy-hubs.yaml) GitHub Actions workflow file:

      - The job named [`upgrade-support`](https://github.com/2i2c-org/infrastructure/blob/41e811931cf1f853c3331d479ca583a342c1c05f/.github/workflows/deploy-hubs.yaml#L198) needs a list of clusters being automatically deployed by our CI/CD system. Add an entry for the new cluster here.
      - If the hub has `staging` in its name (assuming a cluster can have many staging hubs), the job called [`upgrade-staging`](https://github.com/2i2c-org/infrastructure/blob/41e811931cf1f853c3331d479ca583a342c1c05f/.github/workflows/deploy-hubs.yaml#L427) requires a list of staging hubs per cluster. Add an entry for the new staging hub here.

1. **Create a Pull Request with the new hub entry**

   And get a team member to review it.

1. **Merge the PR once it's approved**
   Once you merge the pull request, the GitHub Action workflow will detect that a new entry has been added to the configuration file.

   It will then deploy a new JupyterHub with the configuration you've specified onto the corresponding cluster.

1. **Monitor the action to make sure that it completes**

   If something goes wrong and the workflow does not finish, try [deploying locally](hubs:manual-deploy) to access the logs to help understand what is going on.
   It may be necessary to make new changes to the hub's configuration via a Pull Request, or to *revert* the old Pull Request if you cannot determine how to resolve the problem.

   ```{attention}
   In order to protect sensitive tokens, our CI/CD pipeline will **not** print testing output to its logs.
   You will need to run the [health check locally](hubs:manual-deploy:health-check) to inspect these logs.
   ```

1. **Log in to the hub**

   And ensure that the hub works as expected from a user's perspective.

1. **Send a link to the hub's Community Representative(s)**
   So they can confirm that it works from their perspective as well.
