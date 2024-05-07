(upgrade-cluster:k8s-version-skew)=
# About Kubernetes' version skew policy

When we upgrade our Kubernetes clusters, we upgrade the k8s control plane (k8s
api-server etc.), the cloud providers managed workloads (`calico-node` etc.),
and the k8s node's software (`kubelet` etc.). Since these upgrades aren't done
at the exact same time, there are known constraints on how the various versions
can [_skew_] in relation to each other.

When we upgrade, we are practically constrained by [Kubernetes' version skew
policy] in the following ways:

1. Highly available clusters' control planes can only be upgraded one minor
   version at a time (`api-server` requirement).

   All of our new clusters and most of our old clusters are regional, so our
   documentation assumes we need to respect this constraint.
2. Nodes' k8s version must not be newer than the control plane, and be at most
   three minor versions older (`kubelet` requirement).

[_skew_]: https://www.industrialempathy.com/posts/version-skew/
[Kubernetes' version skew policy]: https://kubernetes.io/releases/version-skew-policy/#supported-version-skew
