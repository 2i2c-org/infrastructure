# Create GCP home-directory disks with gcloud credentials

This document describes how we enable external contributors to use limited credentials to create disks on GCP. This workflow permits certain contributors to stand-up new hubs without 2i2c intervention, without compromising access to other 2i2c projects.

(create-a-home-disk-gcp)=

## Create a home-directory disk

1. Set the `CLUSTER_NAME`, `HUB_NAME` environment variables for convenience:

   ```bash
   # Name of existing cluster
   export CLUSTER_NAME=...
   # Name of new hub
   export HUB_NAME=...
   ```

   This hub must not yet exist.

1. Run the deployer command to create the disk

   ```bash
   deployer exec gcp home-disk "${CLUSTER_NAME}" "${HUB_NAME}" --disk-size=20

   ```

   It will output the necessary configuration changes:

   ```
   # Terraform config:
   "<HUB_NAME>" = {
       size = 20
       name_suffix = "<HUB_NAME>"
   }

   # NFS config:
   # https://infrastructure.2i2c.org/howto/features/storage-quota/#enabling-jupyterhub-home-nfs
   volumeId: projects/<PROJECT>/zones/<ZONE>/disks/hub-nfs-homedirs-<HUB_NAME>
   ```

1. Create a PR that updates the hub configuration and the Terraform configuration with the suggested changes.

## Update Terraform state

Disks created imperatively in [](#create-a-home-disk-gcp) will not be recorded in the Terraform state database. This means that the Terraform state will diverge from the underlying infrastructure, making future replication more difficult. Furthermore, it will not be possible to modify these resources declaratively. As such, it is important to import the state of newly created resources from the cloud provider to the Terraform database.

1. Pull the PR created in [](#create-a-home-disk-gcp) that contains the necessary changes to the Terraform configuration.

1. Navigate to the GCP terraform folder in the infrastructure repo.

   ```bash
   cd terraform/gcp
   ```

1. Select the appropriate Terraform workspace.

   ```bash
   terraform workspace select "${CLUSTER_NAME}"
   ```

1. Set the `CLUSTER_NAME`, `HUB_NAME` environment variables:

   ```bash
   # Name of existing cluster
   export CLUSTER_NAME=...
   # Name of new hub
   export HUB_NAME=...
   ```

1. Set the `VOLUME` variable to the `volumeId` output in [](#create-a-home-disk-gcp).

   ```bash
   VOLUME="projects/<PROJECT>/zones/<ZONE>/disks/hub-nfs-homedirs-<HUB_NAME>"
   ```

1. Import the newly created resource

   ```bash
   terraform import -var-file="projects/${CLUSTER_NAME}.tfvars" $"google_compute_disk.nfs_homedirs[\"${HUB_NAME}\"]" "${VOLUME#projects/}"
   ```

1. Run a plan to ensure that only snapshot policies need to be created:

   ```bash
   terraform plan -var-file="projects/${CLUSTER_NAME}.tfvars"
   ```

1. Apply the plan to create the snapshot policies:
   ```bash
   terraform apply -var-file="projects/${CLUSTER_NAME}.tfvars"
   ```
