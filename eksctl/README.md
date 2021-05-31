### Setup of k8s cluster via eksctl

TODO describe...

### Setup of extras via cloudformation

TODO describe...

### Setup of cluster-autoscaler in the k8s cluster

`eksctl` doesn't automatically install a cluster-autoscaler and it is not part
of a EKS based k8s cluster by itself, so it needs to be manually installed. The
cluster-autoscaler will need permissions to do its job though, and for that we
use some flags in our eksctl config file and then we install it with a Helm
chart.

#### eksctl configuration for cluster-autoscaler

We need our eksctl-cluster-config.yaml to:

1. Declare `nodeGroups.*.iam.withAddonPolicies.autoScaler=true`.
   
   I believe doing so is what makes the following tags automatically be applied
   on node groups, which is required by the cluster-autoscaler to detect them.

   ```
   k8s.io/cluster-autoscaler/<cluster-name>
   k8s.io/cluster-autoscaler/enabled
   ```

2. Declare additional tags for labels/taints.

   ```yaml
   nodeGroups:
     - name: worker-xlarge
       labels:
         k8s.dask.org/node-purpose: worker
       taints:
         k8s.dask.org_dedicated: worker:NoSchedule

       # IMPORTANT: we also provide these tags alongside the labels/taints
       #            to help the cluster-autoscaler do its job.
       #
       tags:
         k8s.io/cluster-autoscaler/node-template/label/k8s.dask.org/node-purpose: worker
         k8s.io/cluster-autoscaler/node-template/taint/k8s.dask.org_dedicated: worker:NoSchedule
   ```


#### Installation of cluster-autoscaler

We rely on the [cluster-autoscaler Helm chart](https://github.com/kubernetes/autoscaler/tree/master/charts/cluster-autoscaler) to manage the k8s resources for the cluster-autoscaler we need to manually complement the k8s cluster with.

```
helm upgrade cluster-autocaler cluster-autoscaler \
    --install \
    --repo https://kubernetes.github.io/autoscaler \
    --version 9.9.2 \
    --namespace kube-system \
    --set autoDiscovery.clusterName=jmte \
    --set awsRegion=us-west-2
```

### Misc

- Create a auth0 application for github
- Update dns record ([jupytearth.org is managed on GCP by Erik](https://console.cloud.google.com/net-services/dns/zones/jupytearth-org/details?folder=&organizationId=&project=domains-sos))

### FIXME: Open questions

- How is cluster-autoscaler acquiring the permissions it needs? Is it by being
  located on the node where we have
  `nodeGroups.*.iam.withAddonPolicies.autoScaler=true`? Then we have ended up
  granting permission to all pods on all nodes that are too high.
