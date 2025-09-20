local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='heliophysics',
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
  nodeGroupGenerations=['b']
);

// Give all notebook nodes 160G disk space rather than the default 80,
// because there are 4 images in use with this hub and they all big!
cluster.withNodeGroupConfigOverride(
  c,
  kind='notebook',
  overrides={
    volumeSize: 160,
  }
)
