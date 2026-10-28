local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.makeCluster(
    name='uw-escience',
    region='us-west-2',
    nodeAz='us-west-2a',
    version='1.36',
    coreNodeInstanceType='r8i-flex.large',
    notebookCPUInstanceTypes=[
      'r5.xlarge',
      'r5.4xlarge',
      'r5.16xlarge',
    ],
    daskInstanceTypes=[],
    hubs=['staging', 'prod'],
    notebookGPUNodeGroups=[
      {
        instanceType: 'g4dn.xlarge',
        gpuType: 'nvidia-tesla-t4',
      },
      {
        instanceType: 'g6.xlarge',
        gpuType: 'nvidia-l4',
      },
      {
        instanceType: 'g5.xlarge',
        gpuType: 'nvidia-a10g',
      },
      {
        instanceType: 'g6e.xlarge',
        gpuType: 'nvidia-l40s',
      },
      {
        instanceType: 'p5.4xlarge',
        gpuType: 'nvidia-h100',
      },
    ],
    nodeGroupGenerations=['a']
  ),
  kind='notebook'
);

c
