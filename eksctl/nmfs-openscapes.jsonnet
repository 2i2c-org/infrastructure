local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.withNodeGroupConfigOverride(
    cluster.makeCluster(
      name='nmfs-openscapes',
      region='us-west-2',
      nodeAz='us-west-2b',
      version='1.34',
      coreNodeInstanceType='r8i-flex.large',
      notebookCPUInstanceTypes=[
        'r5.xlarge',
        'r5.4xlarge',
        'r5.16xlarge',
      ],
      daskInstanceTypes=[
        [
          // Allow for a range of spot instance types
          'r5.4xlarge',
          'r7i.4xlarge',
          'r6i.4xlarge',
        ],
      ],
      hubs=['staging', 'prod', 'workshop', 'noaa-only'],
      notebookGPUNodeGroups=[
        {
          instanceType: 'g4dn.xlarge',
        },
      ],
      nodeGroupGenerations=['c', 'd'],
    ),
    kind='core',
    overrides={ maxSize: 2 }
  ),
  kind='notebook',
  hubName='workshop',
  generation='d',
  overrides={
    // 80 GiB reserved + 4*15GiB (4 users/node)
    volumeSize: 140,
    // Ensure that /tmp is faster
    volumeIOPS: 3000,
    volumeThroughput: 500,
  }
);

c
