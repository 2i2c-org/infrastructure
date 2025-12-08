local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.makeCluster(
    name='earthscope',
    region='us-east-2',
    nodeAz='us-east-2a',
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
    hubs=['staging', 'prod', 'binder'],
    notebookGPUNodeGroups=[
      {
        instanceType: 'g4dn.xlarge',
      },
    ],
    nodeGroupGenerations=['a']
  ),
  // Add provenence of resources
  overrides={
    tags+: {
      'earthscope:application:name': 'geolab',
      'earthscope:application:owner': 'research-onramp-to-the-cloud',
    },
  }
);
c
