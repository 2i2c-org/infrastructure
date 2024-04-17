(new-cluster)=
# Add Kubernetes clusters

The first thing we need in deploying a new hub is a Kubernetes Cluster.
Deploying a new cluster is specific to the cloud provider, though there are many similarities between them all.
This section covers topics in deploying a new Kubernetes Cluster for the major usecases we serve.

(cluster:when-to-deploy)=
## When to deploy a new Kubernetes cluster

Deploying a new cluster is a more complex and costly operation, and generally requires more of our time to upkeep and deploy (and thus, will be more costly to the community).
In general, we'd like hubs to be deployed on pre-existing clusters whenever possible, rather than having a dedicated cluster that is just for the hub's community.

In general, the question of whether to deploy a new cluster for a community comes down to two questions:

- **Whether they need to use their own cloud billing accounts**. This is usually either because they have their own cloud credits that they wish to use, or because they work at an institution that mandates (or otherwise incentivizes) individuals to use institutional cloud accounts.
- **Whether their infrastructure needs require their own cluster**. In some cases a community will need sophisticated infrastructure that requires a dedicated cluster. For example, if they have extreme computational needs, require complex data access, or require different kinds of computing nodes that are not available on clusters that run many different kinds of hubs. For example, [this terraform directory](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/projects) contains configurations for a number of different GCP clusters.

For most hub communities that simply wish to pay for a hub and are not opinionated about the cluster on which it runs, we can deploy their hub on a pre-existing Kubernetes cluster.
In that case, follow the instructions at [](hub-deployment-guide:runbooks:phase3).

The following sections cover how to deploy a Kubernetes cluster.

```{warning}
Deploying Kubernetes to AWS has a distinctly different workflow than GCP or Azure, and therefore it has its own guide.
```

```{toctree}
:maxdepth: 1
:caption: Deploying Kubernetes
new-cluster.md
smce.md
```
