local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='ubc-eoas',
  region='ca-central-1',
  nodeAz='ca-central-1a',
  version='1.34',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    'r5.xlarge',
    'r5.2xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  hubs=[
    'staging',
    'prod',
  ],
  nodeGroupGenerations=['a']
);
c
