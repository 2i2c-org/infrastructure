local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='<< cluster_name >>',
  region='<< cluster_region >>',
  nodeAz='<< cluster_region >>a',
  version='1.34',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    'r5.xlarge',
    'r5.4xlarge',
    'r5.16xlarge',
  ],
  daskInstanceTypes=[
    // Allow for a range of spot instance types
    'r5.4xlarge',
    'r7i.4xlarge',
    'r6i.4xlarge',
  ],
  hubs=[
    <%- for hub in hubs -%>
    '<< hub >>',
    <%- endfor -%>
  ],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a']
);

c
