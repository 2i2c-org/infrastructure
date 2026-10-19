local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='jupyter-health',
  region='us-east-2',
  nodeAz='us-east-2a',
  version='1.36',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    'r5.xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  hubs=['staging', 'prod'],
  // FIXME: once there are no users on the older generation nodes, delete them with:
  // eksctl delete nodegroup --config-file=$cluster.eksctl.yaml --only-missing --approve
  nodeGroupGenerations=['d']
);
c
