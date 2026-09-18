local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='maap',
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
    [
      'r5.4xlarge',
      'r7i.4xlarge',
      'r6i.4xlarge',
    ],
  ],
  hubs=['staging', 'prod'],
  notebookGPUNodeGroups=[
    {
      instanceType: 'g4dn.xlarge',
    },
  ],
  nodeGroupGenerations=['d', 'e'],
);

# jsonnet doesn't like it when we re-use variable
# names, so let's define new variables for each override

# We want larger `/tmp` for larger instances,
# simply as a way to have larger tmp under some
# circumstances. This is hopefully a temporary workaround,
# until we figure out a more permanent way to get larger
# scratch spaces to some users.
local c1 = cluster.withNodeGroupConfigOverride(
  c,
  instanceType='r5.xlarge',
  overrides={
    // For https://github.com/MAAP-Project/Community/issues/1254,
    // so `/tmp` can be larger
    volumeSize: 200,
  }
);

local c2 = cluster.withNodeGroupConfigOverride(
  c1,
  instanceType='r5.4xlarge',
  overrides={
    volumeSize: 400
  }
);


cluster.withNodeGroupConfigOverride(
  c2,
  instanceType='r5.16xlarge',
  overrides={
    volumeSize: 800
  }
)
