local cluster = import './libsonnet/cluster.jsonnet';

cluster.makeCluster(
  name='oceanhackweek-es',
  region='us-west-2',
  nodeAz='us-west-2a',
  version='1.32',
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[
    {
      instanceType: 'g4dn.xlarge',
    },
  ],
  nodeGroupSuffixes=['a']
)
