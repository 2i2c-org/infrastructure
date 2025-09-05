{
  /**
   Create a managed nodegroup config that can autoscale from 0.

   Parameters:
   - clusterName [string]: Name of the EKS cluster this nodeGroup is for
   - namePrefix [string]:
   - instanceType [string]: Type of instance this nodeGroup should contain
   - availabilityZones [array[string]]: List of AZs this nodeGroup should span
   - nameSuffix [string]:
   - minSize [int]: Minimum number of nodes. Also sets desiredCapacity
   - maxSize [int]: Maximum number of nodes
   - extraLabels [dict[string, string]]: Extra labels to add to nodes in this nodeGroup
   - extraTaints [array[dict[string, string]]]: Extra taints to add to nodes in this nodeGroup.
                                                List of dicts with keys 'key', 'value', 'effect'
   - extraTags [dict[string, string]]: Extra resource tags to add to EC2 instances spawned by this nodeGroup
   */
  makeNodeGroup(
    clusterName,
    namePrefix,
    instanceType,
    availabilityZones,
    nameSuffix,
    minSize,
    maxSize,
    extraLabels={},
    extraTaints=[],
    extraTags={}
  ):: {
    /**
     Generate EC2 resource tags representing node labels that cluster autoscaler's autodiscovery understands
     https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup
     */
    local makeCaLabelTags(labels) = {
      ['k8s.io/cluster-autoscaler/node-template/label/%s' % key]: labels[key]
      for key in std.objectFields(labels)
    },
    /**
     Generate EC2 resource tags representing node taints that cluster autoscaler's autodiscovery understands
     https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup
     */
    local makeCaTaintTags(taints) = {
      ['k8s.io/cluster-autoscaler/node-template/taint/%s' % taint.key]: '%s:%s' % [taint.value, taint.effect]
      for taint in taints
    },
    /*
    Private field saving the nameSuffix so withNodeGroupConfigOverride can filter on suffix
    */
    _suffix:: nameSuffix,

    /**
    Construct the name of the nodegroup based on the *prefix*
     */
    // Include name prefix, escaped instance type (because names can't have .)
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
    amiFamily: 'AmazonLinux2023',
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
    nameSuffix,
    minSize,
    maxSize,
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
  ) + {
    iam: {
        withAddonPolicies: {
            # So autoscaler can run here with regular IAM access
            # TODO: Migrate that to IRSA
            autoScaler: true,
        },
    },
    _kind:: 'core',
  },
  makeNotebookCPUNodeGroup(
    clusterName,
    hubName,
    instanceType,
    availabilityZones,
    nameSuffix,
    minSize,
    maxSize,
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
  ) + {
    _kind:: 'notebook',
    _hubName:: hubName,
  },
  makeNotebookGPUNodeGroup(
    clusterName,
    hubName,
    instanceType,
    availabilityZones,
    gpuCount,
    gpuType,
    nameSuffix,
    minSize,
    maxSize
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
    nameSuffix,
    minSize,
    maxSize,
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
        _kind:: 'dask-worker',
        _hubName:: hubName,
        instancesDistribution+: {
          onDemandBaseCapacity: 0,
          onDemandPercentageAboveBaseCapacity: 0,
          spotAllocationStrategy: 'capacity-optimized',
        },
      },
  /**
   Create a valid eksctl Cluster configuration

   Arguments:
   - name [string]: Name of the EKS cluster
   - region [string]: Region the cluster should live in
   - nodeAz [string]: Primary zone the cluster should live in
   - version [string]: Version of EKS control plane + new nodegroups
   - coreNodeInstanceType [string]: Instance Type to be used for core nodes
   - notebookCPUInstanceTypes
   */
  makeCluster(
    name,
    region,
    nodeAz,
    version,
    hubs,
    coreNodeInstanceType,
    notebookCPUInstanceTypes,
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
        coreNodeInstanceType,
        availabilityZones=[nodeAz],
        nameSuffix=suffix,
        minSize=1,
        maxSize=100
      )
      for suffix in nodeGroupSuffixes
    ] + [
      $.makeNotebookCPUNodeGroup(
        clusterName=name,
        availabilityZones=[nodeAz],
        hubName=hubName,
        instanceType=instanceType,
        nameSuffix=suffix,
        minSize=0,
        maxSize=100
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
        nameSuffix=suffix,
        minSize=0,
        maxSize=100
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
        nameSuffix=suffix,
        minSize=0,
        maxSize=100
      )
      for hubName in hubs
      for instanceType in daskInstanceTypes
      for suffix in nodeGroupSuffixes
    ],
  },
  withNodeGroupConfigOverride(
    clusterConfig,
    kind=null,
    hubName=null,
    suffix=null,
    instanceType=null,
    overrides={}
  ):: clusterConfig {
    managedNodeGroups: [
      if (kind == null || ng._kind == kind) && (suffix == null || ng._suffix == suffix) && (hubName == null || std.get(ng, '_hubName', '') == hubName) && (instanceType == null || ng.instanceType == instanceType)
      then ng + overrides
      else ng
      for ng in clusterConfig.managedNodeGroups
    ],
  },
}
