local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='oceanhackweek-es-5',
  region='us-west-2',
  nodeAz='us-west-2a',
  version='1.32',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    'r5.xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[
    {
      instanceType: 'g4dn.xlarge',
    },
  ],
  nodeGroupSuffixes=['a']
  //     {
  //         suffix: 'a',
  //         autoscale: false
  //     },
  //     {
  //         suffix: 'b',
  //         autoscale: true
  //     }
  //   ]
);

cluster.withNodeGroupConfigOverride(
  c,
  kind='core',
  overrides={
    maxSize: 5,
  }
)
