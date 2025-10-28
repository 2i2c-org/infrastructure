local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(

  cluster.makeCluster(
    name='openscapeshub',
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
      // Allow for a range of spot instance types
      ['r5.4xlarge', 'r7i.4xlarge', 'r6i.4xlarge'],
    ],
    hubs=[
      'staging',
      'prod',
      'workshop',
    ],
    notebookGPUNodeGroups=[],
    nodeGroupGenerations=['b', 'c']
  ), kind='core', overrides={ maxSize: 1 }
);
c
