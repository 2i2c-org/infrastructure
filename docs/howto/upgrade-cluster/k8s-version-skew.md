(upgrade-cluster:k8s-version-skew)=
# About Kubernetes' version skew policy

Kubernetes clusters' software running on various machines is designed to work
even when various components gets upgraded independently of each other - at
least as long as the components don't get too mismatched versions.

The _tolerated mismatch of versions between k8s software components_ is called
the supported _version skew_, and Kubernetes provides a [version skew policy]
about this.

Practically for us when upgrading k8s clusters, we need to know that:

1. Highly available clusters' control planes can only be upgraded one minor
   version at a time (`api-server` requirement).

   All of our new clusters and most of our old clusters are highly available, so
   our documentation assumes we need to respect this constraint.
2. Nodes' k8s version must not be newer than the control plane, and be at most
   three minor versions older (`kubelet` requirement).

[version skew policy]: https://kubernetes.io/releases/version-skew-policy/#supported-version-skew
