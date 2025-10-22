local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='nasa-cryo',
  region='us-west-2',
  nodeAz='us-west-2a',
  version='1.33',
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
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[
    {
      instanceType: 'g4dn.xlarge',
    },
  ],
  nodeGroupGenerations=['b']
);

c
