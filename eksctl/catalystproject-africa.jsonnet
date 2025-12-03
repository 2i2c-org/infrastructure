local cluster = import './libsonnet/cluster.jsonnet';

// Turn up maxSize
local c = cluster.withNodeGroupConfigOverride(
  // Increase volumeSize
  cluster.withNodeGroupConfigOverride(
    cluster.makeCluster(
      name='catalystproject-africa',
      region='af-south-1',
      nodeAz='af-south-1a',
      version='1.34',
      coreNodeInstanceType='r5.large',
      notebookCPUInstanceTypes=[
        'r5.xlarge',
        'r5.4xlarge',
        'r5.16xlarge',
      ],
      hubs=[
        'staging',
        'nm-aist',
        'must',
        'uvri',
        'wits',
        'kush',
        'molerhealth',
        'aibst',
        'bhki',
        'bon',
      ],
      nodeGroupGenerations=['b']
    ),
    kind='notebook',
    overrides={ volumeSize: 400 }
  ),
  kind='core',
  overrides={ maxSize: 4 }
);

c
