# Configure per-user storage quotas

This guide explains how to enable and configure per-user storage quotas.

```{note}
Nest all config examples under a `basehub` key if deployingb this for a daskhub.
```

## Enabling jupyter-home-nfs

To be able to configure per-user storage quotas, we need to run an in-cluster NFS server using [`jupyter-home-nfs`](https://github.com/sunu/jupyter-home-nfs). This can be enabled by setting `jupyter-home-nfs.enabled` to `true` in the hub's values file.

jupyter-home-nfs expects a reference to an pre-provisioned disk. Here's an example of how to configure that on AWS and GCP.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
```yaml
jupyter-home-nfs:
  enabled: true
  eks:
    enabled: true
    volumeId: vol-0a1246ee2e07372d0
```
````

````{tab-item} GCP
:sync: gcp-key
```yaml
jupyter-home-nfs:
  enabled: true
  gke:
    enabled: true
    volumeId: projects/jupyter-nfs/zones/us-central1-f/disks/jupyter-nfs-home-directories
```
````
`````

This changes can be deployed by running the following command:

```bash
deployer deploy <cluster_name> <hub_name>
```

Once these changes are deployed, we should have a new NFS server running in our cluster through the `jupyter-home-nfs` Helm chart. We can get the IP address of the NFS server by running the following command:

```bash
kubectl -n <hub_name> get svc <hub_name>-nfs-service
```

To check whether the NFS server is running properly, see the [Troubleshooting](#troubleshooting) section.

## Migrating existing home directories

If there are existing home directories, we need to migrate them to the new NFS server. For this, we will create a throwaway pod with both the existing home directories and the new NFS server mounted, and we will copy the contents from the existing home directories to the new NFS server.

Here's an example of how to do this:

```bash
# Create a throwaway pod with both the existing home directories and the new NFS server mounted
deployer exec root-homes <cluster_name> <hub_name> --extra_nfs_server=<nfs_service_ip> --extra_nfs_base_path=/ --extra_nfs_mount_path=/new-nfs-volume

# Copy the existing home directories to the new NFS server while keeping the original permissions
rsync -av --info=progress2 /root-homes/<path-to-the-parent-of-user-home-directories> /new-nfs-volume/
```

Make sure the path structure of the existing home directories matches the path structure of the home directories in the new NFS storage volume. For example, if an existing home directory is located at `/root-homes/staging/user`, we should expect to find it at `/new-nfs-volume/staging/user`.

## Switching to the new NFS server

Now that we have a new NFS server running in our cluster, and we have migrated the existing home directories to the new NFS server, we can switch the hub to use the new NFS server. This can be done by updating the `basehub.nfs.pv.serverIP` field in the hub's values file.

```yaml
nfs:
  pv:
    serverIP: <nfs_service_ip>
```

Note that Kubernetes doesn't allow changing an existing PersistentVolume. So we need to delete the existing PersistentVolume first.

```bash
   kubectl delete pv ${HUB_NAME}-home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pvc home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pod -l component=shared-dirsize-metrics
   kubectl --namespace $HUB_NAME delete pod -l component=shared-volume-metrics
```

After this, we should be able to deploy the hub and have it use the new NFS server:

```bash
deployer deploy <cluster_name> <hub_name>
```

## Enforcing storage quotas

Now we can set quotas for each user and configure the path to monitor for storage quota enforcement.

This can be done by updating `basehub.jupyter-home-nfs.quotaEnforcer` in the hub's values file. For example, to set a quota of 10GB for the user `staging`, we would add the following to the user's values file:

```yaml
jupyter-home-nfs:
  quotaEnforcer:
    hardQuota: "10" # in GB
    path: "/export/staging"
```

The `path` field is the path to the parent directory of the user's home directory in the NFS server. The `hardQuota` field is the maximum allowed size of the user's home directory in GB.

To deploy the changes, we need to run the following command:

```bash
deployer deploy <cluster_name> <hub_name>
```

Once this is deployed, the hub will automatically enforce the storage quota for each user. If a user's home directory exceeds the quota, the user's pod may not be able to start successfully.

## Troubleshooting

### Checking the NFS server is running properly
To check whether the NFS server is running properly, we can run the following command in the NFS server pod in the nfs-server container:

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

If a user exceeds their quota, the user's pod will not be able to start successfully. A hub admin will need to free up space in the user's home directory to allow the pod to start.