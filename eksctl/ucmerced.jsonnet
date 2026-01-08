local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='ucmerced',
  region='us-west-2',
  nodeAz='us-west-2a',
  version='1.34',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    // Add r5.2xlarge to mirror prior n2-highmem-8 on GCP
    'r5.2xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  daskInstanceTypes=[
    // Allow for a range of spot instance types
    ['r5.4xlarge', 'r7i.4xlarge', 'r6i.4xlarge'],
  ],
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a']
);

c
