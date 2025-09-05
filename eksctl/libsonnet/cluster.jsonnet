{
  makeNodeGroup(
    clusterName,
    namePrefix,
    instanceType,
    availabilityZones,
    nameSuffix='',
    minSize=0,
    maxSize=100,
    extraLabels={},
    extraTaints=[],
    extraTags={}
  ):: {
    local makeCaLabelTags(labels) = {
      ['k8s.io/cluster-autoscaler/node-template/label/%s' % key]: labels[key]
      for key in std.objectFields(labels)
    },
    local makeCaTaintTags(taints) = {
      ['k8s.io/cluster-autoscaler/node-template/taint/%s' % taint.key]: "%s:%s" % [taint.value, taint.effect]
      for taint in taints
    },
    // Include name prefix, filtered instance type (because names can't have .)
    // and name suffix (if given) in the nodegroup name
    name: std.join('-', std.filter(function(x) x != '', [
      namePrefix,
      std.strReplace(instanceType, '.', '-'),
      nameSuffix,
    ])),
    availabilityZones: availabilityZones,
    minSize: minSize,
    maxSize: maxSize,
    desiredCapacity: minSize,
    instanceType: instanceType,
    volumeSize: 80,
    amiFamily: "AmazonLinux2023",
    labels: {
      'node.kubernetes.io/instance-type': instanceType,
    } + extraLabels,
    taints: extraTaints,
    tags: makeCaLabelTags(self.labels) + makeCaTaintTags(self.taints) + {
      ManagedBy: '2i2c',
      '2i2c.org/cluster-name': clusterName,
    } + extraTags,
  },
  makeCoreNodeGroup(
    clusterName,
    instanceType,
    availabilityZones,
    nameSuffix='',
    minSize=1,
    maxSize=10,
  ):: $.makeNodeGroup(
    clusterName=clusterName,
    namePrefix='core',
    instanceType=instanceType,
    availabilityZones=availabilityZones,
    extraLabels={
      'hub.jupyter.org/node-purpose': 'core',
      'k8s.dask.org/node-purpose': 'core',
    },
    extraTags={
      '2i2c:node-purpose': 'core',
    },
    minSize=minSize,
    maxSize=maxSize,
    nameSuffix=nameSuffix
  ),
  makeNotebookCPUNodeGroup(
    clusterName,
    hubName,
    instanceType,
    availabilityZones,
    nameSuffix='',
    minSize=0,
    maxSize=100,
    extraLabels={},
    extraTaints=[],
    extraTags={}
  ):: $.makeNodeGroup(
    clusterName,
    'nb-%s' % [hubName],
    availabilityZones=availabilityZones,
    instanceType=instanceType,
    nameSuffix=nameSuffix,
    minSize=minSize,
    maxSize=maxSize,
    extraLabels={
      'hub.jupyter.org/node-purpose': 'user',
      'k8s.dask.org/node-purpose': 'scheduler',
      '2i2c/hub-name': hubName,
    } + extraLabels,
    extraTaints=[
      {
        key: 'hub.jupyter.org_dedicated',
        value: 'user',
        effect: 'NoSchedule',
      },
      {
        key: 'hub.jupyter.org/dedicated',
        value: 'user',
        effect: 'NoSchedule',
      },
    ] + extraTaints,
    extraTags={
      '2i2c:node-purpose': 'user',
      '2i2c:hub-name': hubName,
    } + extraTags
  ),
  makeNotebookGPUNodeGroup(
    clusterName,
    hubName,
    instanceType,
    availabilityZones,
    gpuCount,
    gpuType,
    nameSuffix='',
    minSize=0,
    maxSize=100
  ):: $.makeNotebookCPUNodeGroup(
    clusterName=clusterName,
    hubName=hubName,
    instanceType=instanceType,
    availabilityZones=availabilityZones,
    nameSuffix=nameSuffix,
    minSize=minSize,
    maxSize=maxSize,
    extraLabels={
      '2i2c/has-gpu': 'true',
      'k8s.amazonaws.com/accelerator': gpuType,
    },
    extraTags={
      'k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu': std.toString(gpuCount),
    },

    extraTaints=[
      {
        key: 'nvidia.com/gpu',
        value: 'present',
        effect: 'NoSchedule',
      },
    ]
  ),
  makeDaskNodeGroup(
    clusterName,
    hubName,
    instanceType,
    availabilityZones,
    nameSuffix='',
    minSize=0,
    maxSize=100
  ):: $.makeNodeGroup(
        clusterName,
        'dask-%s' % [hubName],
        availabilityZones=availabilityZones,
        instanceType=instanceType,
        nameSuffix=nameSuffix,
        minSize=minSize,
        maxSize=maxSize,
        extraLabels={
          'k8s.dask.org/node-purpose': 'worker',
        },

        extraTaints=[
          {
            key: 'k8s.dask.org_dedicated',
            value: 'worker',
            effect: 'NoSchedule',
          },
          {
            key: 'k8s.dask.org/dedicated',
            value: 'worker',
            effect: 'NoSchedule',
          },
        ],
        extraTags={
          '2i2c:node-purpose': 'worker',
        }
      ) +
      {
        instancesDistribution+: {
          onDemandBaseCapacity: 0,
          onDemandPercentageAboveBaseCapacity: 0,
          spotAllocationStrategy: 'capacity-optimized',
        },
      },
  makeCluster(
    name,
    region,
    nodeAz,
    version,
    hubs,
    notebookCPUInstanceTypes=[
      'r5.xlarge',
      'r5.4xlarge',
      'r5.16xlarge',
    ],
    notebookGPUNodeGroups=[],
    daskInstanceTypes=[],
    nodeGroupSuffixes=[]
  ):: {
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
      name: name,
      region: region,
      version: version,
      tags+: {
        ManagedBy: '2i2c',
        '2i2c.org/cluster-name': name,
      },
    },
    availabilityZones: ['%s%s' % [region, i] for i in ['a', 'b', 'c']],
    iam: {
      withOIDC: true,
    },
    cloudWatch: {
      clusterLogging: {
        enableTypes: ['audit', 'api', 'controllerManager', 'scheduler'],
        logRetentionInDays: 7,
      },
    },
    addons: [
      { version: 'latest', tags: {
        ManagedBy: '2i2c',
        '2i2c.org/cluster-name': name,
      } } + addon
      for addon in
        [
          { name: 'coredns' },
          { name: 'kube-proxy' },
          {
            name: 'vpc-cni',
            attachPolicyARNs: ['arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy'],
            // https://github.com/aws/amazon-vpc-cni-k8s/blob/HEAD/charts/aws-vpc-cni/values.yaml
            configurationValues: |||
              enableNetworkPolicy: "false"
            |||,
          },
          {
            name: 'aws-ebs-csi-driver',
            wellKnownPolicies: {
              ebsCSIController: true,
            },
            // We enable detailed metrics collection to watch for issues with
            // jupyterhub-home-nfs
            // https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/HEAD/charts/aws-ebs-csi-driver/values.yaml
            configurationValues: |||
              defaultStorageClass:
                  enabled: true
              controller:
                  enableMetrics: true
              node:
                  enableMetrics: true
            |||,
          },
        ]
    ],
    managedNodeGroups: [
      $.makeCoreNodeGroup(
        name,
        'r5.xlarge',
        availabilityZones=[nodeAz],
        nameSuffix=suffix
      ) for suffix in nodeGroupSuffixes
    ] + [
      $.makeNotebookCPUNodeGroup(
        clusterName=name,
        availabilityZones=[nodeAz],
        hubName=hubName,
        instanceType=instanceType,
        nameSuffix=suffix
      )
      for hubName in hubs
      for instanceType in notebookCPUInstanceTypes
      for suffix in nodeGroupSuffixes
    ] + [
      $.makeNotebookGPUNodeGroup(
        clusterName=name,
        // Default to having GPUs spawn across zones, to increase
        // availability at the cost of some network latency + cross
        // zone traffic costs
        availabilityZones=self.availabilityZones,
        hubName=hubName,
        instanceType=gpuConfig.instanceType,
        gpuCount=std.get(gpuConfig, 'gpuCount', 1),
        gpuType=std.get(gpuConfig, 'gpuType', 'nvidia-tesla-t4'),
        nameSuffix=suffix
      )
      for hubName in hubs
      for gpuConfig in notebookGPUNodeGroups
      for suffix in nodeGroupSuffixes
    ] + [
    ] + [
      $.makeDaskNodeGroup(
        clusterName=name,
        availabilityZones=[nodeAz],
        hubName=hubName,
        instanceType=instanceType,
        nameSuffix=suffix
      )
      for hubName in hubs
      for instanceType in daskInstanceTypes
      for suffix in nodeGroupSuffixes
    ],
  },
}
