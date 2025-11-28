local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='strudel',
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
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a']
);
c
