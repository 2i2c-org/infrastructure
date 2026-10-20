local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.makeCluster(
    name='temple',
    region='us-west-2',
    nodeAz='us-west-2a',
    version='1.36',
    coreNodeInstanceType='r8i-flex.large',
    notebookCPUInstanceTypes=[
      'r5.xlarge',
      'r5.4xlarge',
      'r5.16xlarge',
    ],
    hubs=['staging', 'prod', 'advanced', 'research'],
    notebookGPUNodeGroups=[
      {
        instanceType: 'g4dn.xlarge',
      },
    ],
    // FIXME: once there are no users on the older generation nodes, delete them with:
    // eksctl delete nodegroup --config-file=$cluster.eksctl.yaml --only-missing --approve
    nodeGroupGenerations=['c']
  ),
  kind='core',
  overrides={ maxSize: 2 }
);

c
