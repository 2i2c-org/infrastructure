(migrate-data)=
# Migrate data across NFS servers

This documentation covers how to transfer data between NFS servers in a cloud-agnostic way.

This process should be repeated for as many hubs as there are on the cluster, remembering to update the value of `$HUB_NAME`.

## The initial copy process

```bash
export CLUSTER_NAME=<cluster_name>
export HUB_NAME=<hub_name>
```

1. **Create a pod on the cluster and mount the source and destination NFS servers.**

   We can use the following deployer command to create a pod in the cluster with the two NFS servers mounted.
   The current default NFS will be mounted automatically and we use `--extra-nfs-*` flags to mount the second NFS.

   ```bash
   deployer exec root-homes $CLUSTER_NAME $HUB_NAME \
     --extra-nfs-server=$SERVER_IP \
     --extra-nfs-base-path="/" \
     --extra-nfs-mount-path="dest-fs" \
     --persist
   ```

   - `$SERVER_IP` can be found either through the relevant Cloud provider console, or by running `kubectl --namespace $HUB_NAME get svc` if the second NFS is running `jupyterhub-home-nfs`.
   - The `--persist` flag will prevent the pod from terminating when you exit it, so you can leave the transfer process running.

1. **Install some tools into the pod.**

   We'll need a few extra tools for this transfer so let's install them.

   ```bash
   apt-get update && \
   apt-get install -y rsync parallel screen
   ```

   - `rsync` is what will actually perform the copy
   - `parallel` will help speed up the process by parallelising it
   - `screen` will help the process continue to live in the pod and be protected from network disruptions that would normally kill it

1. **Start a screen session and begin the initial copy process.**

   ```bash
   ls /root-homes/${HUB_NAME}/ | parallel -j4 rsync -ah --progress /root-homes/${HUB_NAME}/{}/ /dest-fs/${HUB_NAME}/{}/
   ```

   ```{admonition} Monitoring tips
   :class: tip

   Start with `-j4`, monitor for an hour or so, and increase the number of threads until you reach high CPU utilisation (low `idle`, high `iowait` from the `top` command).
   ```

   ```{admonition} screen tips
   :class: tip

   To disconnect your `screen` session, you can input {kbd}`Ctrl` + {kbd}`A`, then {kbd}`D` (for "detach").

   To reconnect to a running `screen` session, run `screen -r`.

   Once you have finished with your `screen` session, you can kill it by inputting {kbd}`Ctrl` + {kbd}`A`, then {kbd}`K` and confirming.
   ```

   Once you have detached from `screen`, can now `exit` the pod and let the copy run.

(migrate-data:reattach-pod)=
## Reattaching to the data transfer pod

You can regain access to the pod created for the data transfer using:

```bash
kubectl --namespace $HUB_NAME attach -i ${CLUSTER_NAME}-root-home-shell
```

## Switching the NFS servers over

Once the files have been migrated, we can update the hub(s) to use the new NFS server IP address.

At this point, it is useful to have a few terminal windows open:

- One terminal with `deployer use-cluster-credentials $CLUSTER_NAME` running to run `kubectl` commands in
- Another terminal to run `deployer deploy $CLUSTER_NAME $HUB_NAME` in
- A terminal that is attached to the data transfer pod to re-run the file transfer (see [](migrate-data:reattach-pod))

1. **Check there are no active users on the hub.**
   You can check this by running:

   ```bash
   kubectl --namespace $HUB_NAME get pods -l "component=singleuser-server"
   ```

   If no resources are found, you can proceed to the next step.
   If there are resources, you may wish to wait until these servers have stopped, or coordinate a maintenance window with the community when disruption and potential data loss should be expected.

1. **Make the hub unavailable by deleting the `proxy-public` service.**

   ```bash
   kubectl --namespace $HUB_NAME delete svc proxy-public
   ```

1. **Re-run the `rsync` command in the data transfer pod.**
   This process should take much less time now that the initial copy has completed.

1. **Check the Reclaim Policy of the `Persistent Volume`.**

   We should first verify the [reclaim policy](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming) of the persistent volume to ensure we will not lose any data.

   The reclaim policy can be checked by running:

   ```bash
   kubectl get pv ${HUB_NAME}-home-nfs
   ```

   If the reclaim policy is `Retain`, we are safe to delete the pv without data loss.
   Otherwise, you may need to patch the reclaim policy to change it to `Retain` with:

   ```bash
   kubectl patch pv ${HUB_NAME}-home-nfs -p '{"spec": {"persistentVolumeReclaimPolicy": "Retain"}}'
   ```

1. **Delete the `PersistentVolume` and all dependent objects.**
   `PersistentVolumes` are _not_ editable, so we need to delete and recreate them to allow the deploy with the new IP address to succeed.
   Below is the sequence of objects _dependent_ on the pv, and we need to delete all of them for the deploy to finish.

   ```bash
   kubectl delete pv ${HUB_NAME}-home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pvc home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pod -l component=shared-dirsize-metrics
   kubectl --namespace $HUB_NAME delete pod -l component=shared-volume-metrics
   ```

1. **Update `nfs.pv.serverIP` values in the `<hub-name>.values.yaml` file.**

   ```yaml
   nfs:
     pv:
       serverIP: <nfs_service_ip>
   ```

1. **Run `deployer deploy $CLUSTER_NAME $HUB_NAME`.**
   This should also bring back the `proxy-public` service and restore access.
   You can monitor progress by running:

   ```bash
   kubectl --namespace $HUB_NAME get svc --watch
   ```

Open and merge a PR with these changes so that other engineers cannot accidentally overwrite them.

We can now delete the pod we created to mount the NFS servers:

```bash
kubectl --namespace $HUB_NAME delete pod ${CLUSTER_NAME}-root-home-shell
```
