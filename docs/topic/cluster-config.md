# Cluster configuration reference

At the top level of `hubs.yaml` is a list of **clusters**. Each cluster is a cloud deployment (for example, a Google project) that can have one or more hubs deployed inside it.

Clusters have some basic configurability:

`name`
: A string that uniquely identifies this cluster

`image_repo`
: The base **user image** that all hubs will use in this cluster.

`provider`
: The cloud provider for this cluster (e.g. `gcp`).
