(howto:configure-storage-quota)=
# Configure per-user storage quotas

This guide explains how to enable and configure per-user storage quotas.

```{note}
Nest all config examples under a `basehub` key if deploying this for a daskhub.
```

## Creating a pre-provisioned disk

The in-cluster NFS server uses a pre-provisioned disk to store the users' home directories. We don't use a dynamically provisioned volume because we want to be able to reuse the same disk even when the Kubernetes cluster is deleted and recreated. So the first step is to create a disk that will be used to store the users' home directories.

For infrastructure running on AWS, we can create a disk through Terraform by adding a block like the following to the [tfvars file of the hub](https://github.com/2i2c-org/infrastructure/tree/main/terraform/aws/projects):

```hcl
ebs_volumes = {
  "staging" = {
    size        = 100
    type        = "gp3"
    name_suffix = "staging"
    tags        = {}
  }
}
```

This will create a disk with a size of 100GB for the `staging` hub that we can reference when configuring the NFS server.

## Enabling jupyterhub-home-nfs

To be able to configure per-user storage quotas, we need to run an in-cluster NFS server using [`jupyterhub-home-nfs`](https://github.com/sunu/jupyterhub-home-nfs). This can be enabled by setting `jupyterhub-home-nfs.enabled` to `true` in the hub's values file.

jupyterhub-home-nfs expects a reference to an pre-provisioned disk. Here's an example of how to configure that on AWS and GCP.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
```yaml
jupyterhub-home-nfs:
  enabled: true
  eks:
    enabled: true
    volumeId: vol-0a1246ee2e07372d0
```
````

````{tab-item} GCP
:sync: gcp-key
```yaml
jupyterhub-home-nfs:
  enabled: true
  gke:
    enabled: true
    volumeId: projects/jupyter-nfs/zones/us-central1-f/disks/jupyter-nfs-home-directories
```
````
`````

These changes can be deployed by running the following command:

```bash
deployer deploy <cluster_name> <hub_name>
```

Once these changes are deployed, we should have a new NFS server running in our cluster through the `jupyterhub-home-nfs` Helm chart. We can get the IP address of the NFS server by running the following commands:

```bash
# Authenticate with the cluster
deployer use-cluster-credentials <cluster_name>

# Retrieve the service IP
kubectl -n <hub_name> get svc <hub_name>-nfs-service
```

To check whether the NFS server is running properly, see the [Troubleshooting](#troubleshooting) section.

## Migrating existing home directories

If there are existing home directories, we need to migrate them to the new NFS server. For this, we will create a throwaway pod with both the existing home directories and the new NFS server mounted, and we will copy the contents from the existing home directories to the new NFS server.

Here's an example of how to do this:

```bash
# Create a throwaway pod with both the existing home directories and the new NFS server mounted
deployer exec root-homes <cluster_name> <hub_name> --extra-nfs-server=<nfs_service_ip> --extra-nfs-base-path=/ --extra-nfs-mount-path=/new-nfs-volume

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

This can be done by updating `basehub.jupyterhub-home-nfs.quotaEnforcer` in the hub's values file. For example, to set a quota of 10GB for all users on the `staging` hub, we would add the following to the hub's values file:

```yaml
jupyterhub-home-nfs:
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

## Enabling alerting through Prometheus Alertmanager

Once we have enabled storage quotas, we want to be alerted when the disk usage of the NFS server exceeds a certain threshold so that we can take appropriate action.

To do this, we need to create a Prometheus rule that will alert us when the disk usage of the NFS server exceeds a certain threshold using Alertmanager. 

First, we need to enable Alertmanager in the hub's support values file (for example, [here's the one for the `nasa-veda` cluster](https://github.com/2i2c-org/infrastructure/blob/main/config/clusters/nasa-veda/support.values.yaml)).

```yaml
prometheus:
  alertmanager:
    enabled: true
```

Then, we need to create a Prometheus rule that will alert us when the disk usage of the NFS server exceeds a certain threshold. For example, to alert us when the disk usage of the NFS server exceeds 90% of the total disk size, we would add the following to the hub's support values file:

```yaml
prometheus:
  serverFiles:
    alerting_rules.yml:
      groups:
        - name: <cluster_name> jupyterhub-home-nfs EBS volume full
          rules:
            - alert: jupyterhub-home-nfs-ebs-full
              expr: node_filesystem_avail_bytes{mountpoint="/shared-volume", component="shared-volume-metrics"} / node_filesystem_size_bytes{mountpoint="/shared-volume", component="shared-volume-metrics"} < 0.1
              for: 15m
              labels:
                severity: critical
                channel: pagerduty
                cluster: <cluster_name>
              annotations:
                summary: "jupyterhub-home-nfs EBS volume full in namespace {{ $labels.namespace }}"
```

And finally, we need to configure Alertmanager to send alerts to PagerDuty.

```yaml
prometheus:
  alertmanager:
    enabled: true
    config:
      route:
        group_wait: 10s
        group_interval: 5m
        receiver: pagerduty
        repeat_interval: 3h
        routes:
          - receiver: pagerduty
            match:
              channel: pagerduty
```


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

If a user exceeds their quota, the user's pod will not be able to start successfully. A hub admin will need to free up space in the user's home directory to allow the pod to start, using [the `allusers` feature](topic:storage:allusers).
