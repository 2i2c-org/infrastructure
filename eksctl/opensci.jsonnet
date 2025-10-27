local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='opensci',
  region='us-west-2',
  nodeAz='us-west-2a',
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
    'sciencecore',
    'climaterisk',
    'small-binder',
    'big-binder',
  ],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a']
);

c
