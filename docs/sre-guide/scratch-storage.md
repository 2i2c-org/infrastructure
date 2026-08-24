(scratch-storage)=
# Setting up scratch storage with emptyDir

Because the hub home storage is based on NFS, it's only supposed to be used for storing small data and code. Storing large datasets is not recommended because it can get expensive and inefficient pretty quickly. Instead, we recommend using cloud object storage combined with scratch storage that is local to the node where the notebook server is running.

This guide covers how to setup a scratch storage in `/tmp` using an `emptyDir` volume and how to reason about choosing the right performance and size.

`````{tab-set}
````{tab-item} ## AWS
:sync: aws-key

### Choosing the right disk size

By default, we size [the node's root disk to 80GB](https://github.com/2i2c-org/infrastructure/blob/befc7c85d998e6e712873fdd0c972312bc5802dc/eksctl/libsonnet/cluster.jsonnet#L76) to make sure we can fit the OS, container images and any kubelet data, with enough headroom to avoid node DiskPressure.

If we were to know that a user is going to need about 10GB of scratch storage, then, to this default disk size of 80GB we'll have to add 10GB x the number of users that will be running on the same node.

Let's say we have 4 users per node, then the total disk size should be 80GB + 10GB * 4 = 120GB. This is the value that should be set in the `volumeSize` field of the node's type.

### Choosing the right disk performance

In addition to the disk size, there are two more metrics that we care about and we can configure:
the volume IOPS and the volume throughput.

By default, with an EBS gp3 volume, we get 3,000 IOPS and 125 MB/s throughput at no additional cost. For an additional fee, these defaults can be configured up to 80,000 IOPS and 2,000 MB/s throughput for a gp3volume per https://aws.amazon.com/ebs/general-purpose.

```{important}
HOWEVER, the overall performance of an EBS volume is bounded by the instance type's performance limits, or the aggregated performance of its attached volumes, whichever is smaller.

This means that the actual max IOPS and throughput that we can configure will depend on the node's instance type.
Checkout https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-optimized.html for more information on the instance type's performance limits.
```

So, for an `r5.4xlarge` that can fit 4 users, the maximum throughput we can set is 590 MB/s. If we were to need a higher throughput, we would have to consider using a different instance type and/or a different node packing strategy.

### Setup the disk size and performance

Inside the cluster's `jsonnet` configuration, configure the root EBS volume size and performance (volume IOPS, volume throughput).

```
local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(...);

cluster.withNodeGroupConfigOverride(
  c,
  kind='notebook',
  hubName='workshop',
  generation='e',
  overrides={
    // 80 GiB reserved + 4*10GiB (4 users/node)
    volumeSize: 120,
    volumeIOPS: 3000,
    volumeThroughput: 590,
  }
)
```
````
`````

## Setup the singleuser scratch storage with emptyDir

For each user, mount this scratch storage at `/tmp` using an `emptyDir` volume and setup a quota to prevent users from using too much of the node's disk space, causing other pods to be evicted.

```yaml
singleuser:
  storage:
    extraVolumes:
      01-scratch-session:
        name: scratch-session
        emptyDir:
          sizeLimit: 10Gi
    extraVolumeMounts:
      01-scratch-session:
        name: scratch-session
        mountPath: /tmp
```
