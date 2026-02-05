local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.makeCluster(
    name='temple',
    region='us-west-2',
    nodeAz='us-west-2a',
    version='1.34',
    coreNodeInstanceType='r8i-flex.large',
    notebookCPUInstanceTypes=[
      'r5.xlarge',
      'r5.4xlarge',
      'r5.16xlarge',
    ],
    hubs=['staging', 'prod', 'advanced', 'research'],
    notebookGPUNodeGroups=[
      {
        instanceType: 'g4dn.xlarge',
      },
    ],
    nodeGroupGenerations=['a', 'b']
  ),
  kind='core',
  overrides={ maxSize: 2 }
);

c
