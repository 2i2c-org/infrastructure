(scratch-storage)=
# Setting up scratch storage with emptyDir

The NFS based home storage that we have setup four our hubs is supposed to be used for storing small data and code. Is not meant to be used for storing large datasets because it can get expensive and inefficient pretty quickly. 
Instead, for larger datasets, we recommend using cloud object storage combined with scratch storage that is local to the node where the notebook server is running.

This guide covers how to setup a scratch storage in `/tmp` using and `emptyDir` volume and how to reason about choosing the right performance and size.

## Common config

## AWS

Configure the EBS volume that's going to be used for scratch inside the cluster's `jsonnet` configuration.

```
local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(...);

cluster.withNodeGroupConfigOverride(
  c,
  kind='notebook',
  hubName='workshop',
  generation='e',
  overrides={
    // 18 GiB reserved + 4*15GiB (4 users/node)
    volumeSize: 78,
    // Ensure that /tmp is faster
    volumeIOPS: 3000,
    volumeThroughput: 590,
  }
)
```

