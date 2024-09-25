# Resizing Prometheus' disk

We may need to resize Prometheus' disk that collects metrics data as we store more and more data.

On GCP clusters, the storage classes are set by default to permit auto-expansion.
Therefore, simply defining a new persistent volume size in the support chart values and redeploying it, should suffice.
However, this may not be the case on other cloud providers.
The below steps will walk you through resizing the disk.

## Resizing the disk

```bash
# Set the KUBE_EDITOR env var to point to a text editor you're comfortable with
export KUBE_EDITOR="/usr/bin/nano"

# Set the name of the cluster to work against
export CLUSTER_NAME=...

# Authenticate against the cluster
deployer use-cluster-credentials $CLUSTER_NAME
```

1. Set the desired size of the Prometheus server persistent volume in the relevant `support.values.yaml` file.

   ```yaml
   prometheus:
     server:
       persistentVolume:
         size: <desired-size>
   ```

1. Check the reclaim policy on the persistent volume.

   ```bash
   # List all the PVs. They are not namespaced.
   kubectl get pv
   ```

1. Edit persistent volume's reclaim policy to be `Retain` if it is not already.
   This will prevent us from losing the data Prometheus has already collected.

   ```bash
   kubectl edit pv <pv-name>
   ```

1. Check the value of `ALLOWVOLUMEEXPANSION` of the default storage class, identified by `(default)` next to it's name.

   ```bash
   kubectl get storageclass
   ```

1. Set `ALLOWVOLUMEEXPANSION` to `true` if it is not.
   This will allow the persistent volumes to be dynamically resized.

   ```bash
   kubectl patch storageclass <storage-class-name> --patch '{\"allowVolumeExpansion\": true}'
   ```

```{note}
At the point, you could try to redeploy the support chart and see if it succeeds.
If it doesn't, continue with the steps.
```

1. Delete the persistent volume claim for the prometheus server.
   Persistent volume claims cannot be patched so we will need to recreate it.

   ```bash
   # List all PVCs in the support namespace
   kubectl -n support get pvc

   # Delete the prometheus server PVC
   kubectl -n support delete pvc support-prometheus-server
   ```

1. In another terminal with the `CLUSTER_NAME` variable set, redeploy the support chart.
   It should fail with the PVC in a `Pending` state.

   ```bash
   deployer deploy-support $CLUSTER_NAME
   ```

1. Edit the persistent volume to have the same UID and resource version as the newly created PVC under`spec.claimRef`.

   ```bash
   # Get the UID and resource version of the PVC
   kubectl -n support get pvc support-prometheus-server -o yaml

   # Edit the PV to reference these values under `spec.claimRef`
   kubectl edit pv <pv-name>
   ```

1. Delete the prometheus server pod and check that it comes back up.

   ```bash
   kubectl -n support delete pod support-prometheus-server-<hash>
   kubectl -n support get pods --watch
   ```

1. Redeploy the support chart again and this time it should succeed.

   ```bash
   deployer deploy-support $CLUSTER_NAME
   ```
