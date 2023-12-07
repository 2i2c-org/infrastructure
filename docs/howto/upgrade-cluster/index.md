(upgrade-cluster)=
# Upgrade Kubernetes clusters

How we upgrade a Kubernetes cluster is specific to the cloud provider. This
section covers topics in upgrading an existing Kubernetes cluster.

```{warning}
As of now, we also only have written documentation for how to upgrade Kubernetes
clusters on AWS.
```

## Upgrade policy

We aim to ensure we use a k8s version for the control plane and node groups that is at least **five minor versions** behind the latest one available at any given time.

Ideally, the following rules should also be respected:

1. Every new cluster we deploy should be using the latest available kubernetes version.
1. All of the clusters deployed in a cloud provider should be using the same version.
1. Check if new upgrades are needed at least every 3 months.


```{warning}
As of now, we have not yet established practices on how to ensure these upgrades happen according to the policy above. Establishing this is tracked in [this GitHub
issue](https://github.com/2i2c-org/infrastructure/issues/412).
```

```{toctree}
:maxdepth: 1
:caption: Upgrading Kubernetes clusters
aws.md
```
