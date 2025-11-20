local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='jupyter-health',
  region='us-east-2',
  nodeAz='us-east-2a',
  version='1.34',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    'r5.xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  hubs=['staging', 'prod'],
  nodeGroupGenerations=['b']
);
c
