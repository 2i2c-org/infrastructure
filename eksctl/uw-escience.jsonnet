local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.makeCluster(
    name='uw-escience',
    region='us-west-2',
    nodeAz='us-west-2a',
    version='1.34',
    coreNodeInstanceType='r8i-flex.large',
    notebookCPUInstanceTypes=[
      'r5.xlarge',
      'r5.4xlarge',
      'r5.16xlarge',
    ],
    daskInstanceTypes=[],
    hubs=['staging', 'prod'],
    notebookGPUNodeGroups=[
      {
        instanceType: 'g4dn.xlarge',
      },
    ],
    nodeGroupGenerations=['a', 'b']
  ),
  kind='notebook',
  overrides={
    // 80 GiB reserved + 4*100GiB (four users)
    volumeSize: 480,
    // Ensure that /tmp is faster
    volumeIOPS: 4000,
    volumeThroughput: 300,
  }
);

c
