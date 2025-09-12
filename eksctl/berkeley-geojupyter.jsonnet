local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='berkeley-geojupyter',
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
    'r5.4xlarge',
  ],
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['c']
);

c
