local cluster = import './libsonnet/cluster.jsonnet';

local _c = cluster.makeCluster(
  name='nasa-veda',
  region='us-west-2',
  nodeAz='us-west-2a',
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
  nodeGroupGenerations=['c'],
);
// Turn up maxSize
local c = cluster.withNodeGroupConfigOverride(
  _c, kind='core', overrides={ maxSize: 2 }
);
c
