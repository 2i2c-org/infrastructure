local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='schmidt-astro-events',
  region='us-east-1',
  nodeAz='us-east-1a',
  version='1.36',
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
    ]
  ],
  hubs=['staging','workshop',],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a'],
  extraTags={
    "JHCM:Attributable": "true",
    "JHCM:ClusterName": "schmidt-astro-events"
  }
);

c