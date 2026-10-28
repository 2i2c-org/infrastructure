local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.makeCluster(
  name='schmidt-astro-events',
  region='us-east-1',
  nodeAz='us-east-1a',
  version='1.36',
  coreNodeInstanceType='r8i-flex.large',
  notebookCPUInstanceTypes=[
    # Keep both m and r instances here, so we can switch just in common.yaml
    'm8i.xlarge',
    'm8i.2xlarge',
    'm8i.4xlarge',
    'm8i.16xlarge',
    'r8i.xlarge',
    'r8i.2xlarge',
    'r8i.4xlarge',
    'r8i.16xlarge',
  ],
  daskInstanceTypes=[
    [
      // Allow for a range of spot instance types
      'r5.4xlarge',
      'r7i.4xlarge',
      'r6i.4xlarge',
    ],
  ],
  hubs=['staging', 'workshop'],
  notebookGPUNodeGroups=[],
  nodeGroupGenerations=['a'],
  extraTags={
    'JHCM:Attributable': 'true',
    'JHCM:ClusterName': 'schmidt-astro-events',
  },
  extraAddons=[
    {
      name: 'aws-efs-csi-driver',
      serviceAccountRoleARN: 'arn:aws:iam::998493219388:role/schmidt-astro-events-s3files-efs-csi-driver',
    },
  ]
);

c
