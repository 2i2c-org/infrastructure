(upgrade-cluster)=
# Upgrade Kubernetes clusters

How we upgrade a Kubernetes cluster is specific to the cloud provider. This
section covers topics in upgrading an existing Kubernetes cluster.

```{warning}
As of now, we are lacking written documentation for how to upgrade Kubernetes
clusters on GCP.
```

(upgrade-cluster:planning)=
## Upgrade planning

```{warning}
We haven't yet established a policy for planning and communicating maintenance
procedures to community champions and users.

Up until now we have made some k8s cluster upgrades opportunistically,
especially for clusters that has showed little to no activity during some
periods. Other cluster upgrades have been scheduled with community champions, and
some in shared clusters have been announced ahead of time.
```

(upgrade-cluster:ambition)=
## Upgrade ambition

1. To keep our k8s cluster's control plane and node pools upgraded to the latest
   _three_ and _four_ [official minor k8s versions] respectively at all times.
2. To await a level of maturity for minor k8s versions before we adopt them.

   | Kubernetes distribution | Our maturity criteria                     |
   | -                       | -                                         |
   | GKE                     | Part of [GKE's regular release channel]   |
   | EKS                     | [Supported by `eksctl`] and is GKE mature |
   | AKS                     | Listed as [generally available on AKS]    |
3. To upgrade k8s cluster's control plane and node pools at least _twice_ and
   _once_ per year respectively.
4. To not disrupt user nodes with running users, by instead rolling out new user
   node pools if needed and cleaning up the old at a later time.
5. To check if actions needs to be scheduled related to this in the beginning of
   every quarter.

[official minor k8s versions]: https://kubernetes.io/releases/
[gke's regular release channel]: https://cloud.google.com/kubernetes-engine/docs/release-notes-regular
[supported by `eksctl`]: https://eksctl.io/getting-started/#basic-cluster-creation
[generally available on aks]: https://learn.microsoft.com/en-gb/azure/aks/supported-kubernetes-versions?tabs=azure-cli#aks-kubernetes-release-calendar

```{toctree}
:maxdepth: 1
:caption: Upgrading Kubernetes clusters
upgrade-disruptions.md
node-upgrade-strategies.md
k8s-version-skew.md
aws.md
azure.md
```
