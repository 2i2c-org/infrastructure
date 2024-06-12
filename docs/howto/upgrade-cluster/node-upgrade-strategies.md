(upgrade-cluster:node-upgrade-strategies)=

# About strategies to upgrade nodes

## About rolling upgrades

To upgrade node group's nodes, we typically do *rolling upgrades*. In a rolling
upgrade, something new is added to replace something old before its removed.

When doing a rolling upgrade of node groups, we can do a rolling upgrade _fast
and forcefully_ or _slow and patiently_ - either pods running on a node group's
nodes get forcefully stopped, or they get to stop on their own.

*Managed* node groups can do fast and forceful rolling upgrades, while
*unmanaged* node groups need to be re-created to get upgraded k8s software
(`kubelet` etc).

Core nodes' workloads can be suitable to forcefully relocate, while user nodes'
workloads should be given time to stop on their own.

## About re-creation upgrades

With unmanaged node groups like on EKS, if disruption isn't a concern or if
there isn't anything running to disrupt, node groups can be deleted and
re-created to save time.
