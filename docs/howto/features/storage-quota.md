(howto:configure-storage-quota)=

# Configure per-user storage quotas

This guide explains how to enable and configure per-user storage quotas using the `jupyterhub-home-nfs` helm chart.

```{note}
Nest all config examples under a `basehub` key if deploying this for a daskhub.
```

## Creating a pre-provisioned disk

The in-cluster NFS server uses a pre-provisioned disk to store the users' home directories. We don't use a dynamically provisioned volume because we want to be able to reuse the same disk even when the Kubernetes cluster is deleted and recreated. So the first step is to create a disk that will be used to store the users' home directories.

For infrastructure running on AWS, we can create a disk through Terraform by adding a block like the following to the [`tfvars` file of the cluster](https://github.com/2i2c-org/infrastructure/tree/main/terraform/aws/projects):

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
```
ebs_volumes = {
  "staging" = {
    size        = 100  # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name": "staging" }
  }
}
```
````
````{tab-item} GCP
:sync: gcp-key
```
persistent_disks = {
  "staging" = {
    size        = 100  # in GB
    name_suffix = "staging"
  }
}
```
````
````{tab-item} Jetstream2
:sync: jetstream2-key
```
persistent_disks = {
  "staging" = {
    size        = 100  # in GB
    name_suffix = "staging"
    tags        = { "2i2c:hub-name": "staging" }
  }
}
```
````
`````

This will create a disk with a size of 100GB for the `staging` hub that we can reference when configuring the NFS server.

Apply these changes with:

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

```{important}
At this point, it is also a good idea to enable [automatic backups of the the NFS server](howto:filesystem-backups:enable:aws) as well.
```

## Enabling `jupyterhub-home-nfs`

To be able to configure per-user storage quotas, we need to run an in-cluster NFS server using [`jupyterhub-home-nfs`](https://github.com/sunu/jupyterhub-home-nfs). This can be enabled by setting `jupyterhub-home-nfs.enabled = true` in the hub's values file (or the common values files if all hubs on this cluster will be using this).

`jupyterhub-home-nfs` expects a reference to an pre-provisioned disk.
You can retrieve the `volumeId` by checking the Terraform outputs:

```bash
terraform output
```

Here's an example of how to connect the volume to `jupyterhub-home-nfs` on AWS and GCP in the hub values file.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
```yaml
jupyterhub-home-nfs:
  enabled: true  # can be migrated to common values file
  eks:
    enabled: true  # can be migrated to common values file
    volumeId: vol-0a1246ee2e07372d0
```
````

````{tab-item} GCP
:sync: gcp-key
```yaml
jupyterhub-home-nfs:
  enabled: true  # can be migrated to common values file
  gke:
    enabled: true  # can be migrated to common values file
    volumeId: projects/jupyter-nfs/zones/us-central1-f/disks/jupyter-nfs-home-directories
```
````

````{tab-item} Jetstream2
:sync: jetstream2-key
```yaml
jupyterhub-home-nfs:
  enabled: true  # can be migrated to common values file
  openstack:
    enabled: true  # can be migrated to common values file
    volumeId: 694b2c04-6b08-4ebe-8cb9-74f7d42c1b1c
```
````
`````

These changes can be deployed by running the following command:

```bash
deployer deploy $CLUSTER_NAME $HUB_NAME
```

Once these changes are deployed, we should have a new NFS server running in our cluster through the `jupyterhub-home-nfs` Helm chart. We can get the IP address of the NFS server by running the following commands:

```bash
# Authenticate with the cluster
deployer use-cluster-credentials $CLUSTER_NAME

# Retrieve the service IP
kubectl -n $HUB_NAME get svc ${HUB_NAME}-nfs-service
```

To check whether the NFS server is running properly, see the [Troubleshooting](#troubleshooting) section.

## Migrating existing home directories and switching to the new NFS server

See [](migrate-data) for instructions on performing these steps.

## Enforcing storage quotas

(global-storage-quotas)=

### Global storage quotas

````{warning}
If you attempt to enforce quotas before having performed the migration, you may see the following error:

```bash
FileNotFoundError: [Errno 2] No such file or directory: '/export/$HUB_NAME'
```
````

Now we can set quotas for each user and configure the path to monitor for storage quota enforcement.

```{tip} Deciding upon a reasonable quota

We should set _reasonable_ quota limits. As of writing, that means a small limit for most users. If you're not sure, choose 10GB per user. For research hubs, this figure is likely much higher (e.g. 100GB/user). Specific users *may* have exceptions made with custom quotas.
```

This can be done by updating `basehub.jupyterhub-home-nfs.quotaEnforcer` in the hub's values file. For example, to set a quota of 10GB for all users on the `staging` hub, we would add the following to the hub's values file:

```yaml
jupyterhub-home-nfs:
  quotaEnforcer:
    config:
      QuotaManager:
        hard_quota: 10 # in GB
```

The `path` field is the path to the parent directory of the user's home directory in the NFS server. The `hard_quota` field is the maximum allowed size of the user's home directory in GB.

To deploy the changes, we need to run the following command:

```bash
deployer deploy $CLUSTER_NAME $HUB_NAME
```

Once this is deployed, the hub will automatically enforce the storage quota for each user. If a user's home directory exceeds the quota, the user's pod may not be able to start successfully.

### Per-user quotas

Most users may have similar storage needs and it is reasonable to impose the same storage constraints upon them. There may, however, be some users that have legitimate additional storage needs. We can accommodate such users by adding _overrides_ to the storage quota system.

```{warning} User IDs are secrets!
It is important to set per-user storage quotas as [secrets using sops](#secrets-and-private-keys). User IDs are personal identifiable information, and our infrastructure repository is publicly visible.

```

```yaml
jupyterhub-home-nfs:
  quotaEnforcer:
    config:
      QuotaManager:
        quota_overrides:
          "foo-bar": 100 # in GB
```

The keys under ``basehub.jupyterhub-home-nfs.quotaEnforcer.config.QuotaManager.quota_overrides` must be the names of directories under the top-level path(s) managed by `jupyterhub-home-nfs`. This configuration may be deployed using the strategy outlined in [](#global-storage-quotas)

## Increasing the size of the disk used by the NFS server

If the disk used by the NFS server is close to being full, we may need to increase its size. This can be done by following the instructions in [](howto:increase-disk-size).

## Troubleshooting

### Checking the NFS server is running properly

To check whether the NFS server is running properly, get a shell inside the the NFS server pod in the nfs-server container with:

```bash
kubectl -n <namespace> exec --stdin --tty <nfs-server-pod> -c nfs-server -- /bin/bash
```

and run the following command:

```bash
showmount -e 0.0.0.0
```

If the NFS server is running properly, we should see the path to the NFS server's export directory. For example:

```bash
Export list for 0.0.0.0:
/export *
```

If we don't see the path to the export directory, the NFS server is not running properly and we need to check the logs for the NFS server pod.

### Debugging quota enforcement

We can check the current usage and quotas for each user by running the following command in the NFS server pod in the `enforce-xfs-quota` container:

```bash
xfs_quota -x -c 'report -N -p'
```

This should show us the list of directories being monitored for quota enforcement, and the current usage and quotas for each of the home directories.

If a user exceeds their quota, the user's pod will not be able to start successfully. A hub admin will need to free up space in the user's home directory to allow the pod to start, using [the `allusers` feature](topic:storage:allusers).
