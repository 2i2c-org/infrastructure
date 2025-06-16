/*
    This file is a jsonnet template of a eksctl's cluster configuration file,
    that is used with the eksctl CLI to both update and initialize an AWS EKS
    based cluster.

    This file has in turn been generated from eksctl/template.jsonnet which is
    relevant to compare with for changes over time.

    To use jsonnet to generate an eksctl configuration file from this, do:

        jsonnet << cluster_name >>.jsonnet > << cluster_name >>.eksctl.yaml

    References:
    - https://eksctl.io/usage/schema/
*/
local ng = import './libsonnet/nodegroup.jsonnet';

// place all cluster nodes here
local clusterRegion = '<< cluster_region >>';
local masterAzs = ['<< cluster_region >>a', '<< cluster_region >>b', '<< cluster_region >>c'];
local nodeAz = '<< cluster_region >>a';

// Node definitions for notebook nodes. Config here is merged
// with our notebook node definition.
// A `node.kubernetes.io/instance-type label is added, so pods
// can request a particular kind of node with a nodeSelector
local notebookNodes = [
<% for hub in hubs %>
  // << hub >>
  {
    instanceType: 'r5.xlarge',
    namePrefix: 'nb-<< hub >>',
    labels+: { '2i2c/hub-name': '<< hub >>' },
    tags+: { '2i2c:hub-name': '<< hub >>' },
  },
  {
    instanceType: 'r5.4xlarge',
    namePrefix: 'nb-<< hub >>',
    labels+: { '2i2c/hub-name': '<< hub >>' },
    tags+: { '2i2c:hub-name': '<< hub >>' },
  },
  {
    instanceType: 'r5.16xlarge',
    namePrefix: 'nb-<< hub >>',
    labels+: { '2i2c/hub-name': '<< hub >>' },
    tags+: { '2i2c:hub-name': '<< hub >>' },
  },
<% endfor %>
<% if gpu_nodes %>
<% for hub in gpu_hubs %>
  {
    instanceType: 'g4dn.xlarge',
    namePrefix: 'gpu-<< hub >>',
    minSize: 0,
    labels+: {
      '2i2c/hub-name': '<< hub >>',
      '2i2c/has-gpu': 'true',
    },
    tags+: {
      'k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu': '1',
      '2i2c:hub-name': '<< hub >>',
    },
    taints+: {
      'nvidia.com/gpu': 'present:NoSchedule',
    },
    // Allow provisioning GPUs across all AZs, to prevent situation where all
    // GPUs in a single AZ are in use and no new nodes can be spawned
    availabilityZones: masterAzs,
  },
<% endfor %>
<% endif %>
];

<% if dask_nodes %>
local daskNodes = [
  // Node definitions for dask worker nodes. Config here is merged
  // with our dask worker node definition, which uses spot instances.
  // A `node.kubernetes.io/instance-type label is set to the name of the
  // *first* item in instanceDistribution.instanceTypes, to match
  // what we do with notebook nodes. Pods can request a particular
  // kind of node with a nodeSelector
  //
  // A not yet fully established policy is being developed about using a single
  // node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
  //
<% for hub in dask_hubs %>
  {
    namePrefix: 'dask-<< hub >>',
    labels+: { '2i2c/hub-name': '<< hub >>' },
    tags+: { '2i2c:hub-name': '<< hub >>' },
    instancesDistribution+: { instanceTypes: ['r5.4xlarge'] },
  },
<% endfor %>
];
<% else %>
local daskNodes = [];
<% endif %>


{
  apiVersion: 'eksctl.io/v1alpha5',
  kind: 'ClusterConfig',
  metadata+: {
    name: '<< cluster_name >>',
    region: clusterRegion,
    {#
        version should be the latest support version by the eksctl CLI, see
        https://eksctl.io/getting-started/ for a list of supported versions.
    -#}
    version: '1.32',
    tags+: {
      ManagedBy: '2i2c',
      '2i2c.org/cluster-name': $.metadata.name,
    },
  },
  availabilityZones: masterAzs,
  iam: {
    withOIDC: true,
  },
  // If you add an addon to this config, run the create addon command.
  //
  //    eksctl create addon --config-file=<< cluster_name >>.eksctl.yaml
  //
  addons: [
    { version: 'latest', tags: $.metadata.tags } + addon
    for addon in
      [
        { name: 'coredns' },
        { name: 'kube-proxy' },
        {
          // vpc-cni is a Amazon maintained container networking interface
          // (CNI), where a CNI is required for k8s networking. The aws-node
          // DaemonSet in kube-system stems from installing this.
          //
          // Related docs: https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/
          //               https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html
          //
          name: 'vpc-cni',
          attachPolicyARNs: ['arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy'],
          // configurationValues ref: https://github.com/aws/amazon-vpc-cni-k8s/blob/HEAD/charts/aws-vpc-cni/values.yaml
          configurationValues: |||
            enableNetworkPolicy: "false"
          |||,
        },
        {
          // aws-ebs-csi-driver ensures that our PVCs are bound to PVs that
          // couple to AWS EBS based storage, without it expect to see pods
          // mounting a PVC failing to schedule and PVC resources that are
          // unbound.
          //
          // Related docs: https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html
          //
          name: 'aws-ebs-csi-driver',
          wellKnownPolicies: {
            ebsCSIController: true,
          },
          // We enable detailed metrics collection to watch for issues with
          // jupyterhub-home-nfs
          // configurationValues ref: https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/HEAD/charts/aws-ebs-csi-driver/values.yaml
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
  nodeGroups: [
    n { clusterName: $.metadata.name }
    for n in
      [
        ng {
          namePrefix: 'core',
          nameSuffix: 'a',
          nameIncludeInstanceType: false,
          availabilityZones: [nodeAz],
          instanceType: 'r5.xlarge',
          minSize: 1,
          maxSize: 6,
          labels+: {
            'hub.jupyter.org/node-purpose': 'core',
            'k8s.dask.org/node-purpose': 'core',
          },
          tags+: {
            '2i2c:node-purpose': 'core',
          },
        },
      ] + [
        ng {
          namePrefix: 'nb',
          availabilityZones: [nodeAz],
          minSize: 0,
          maxSize: 500,
          instanceType: n.instanceType,
          labels+: {
            'hub.jupyter.org/node-purpose': 'user',
            'k8s.dask.org/node-purpose': 'scheduler',
          },
          taints+: {
            'hub.jupyter.org_dedicated': 'user:NoSchedule',
            'hub.jupyter.org/dedicated': 'user:NoSchedule',
          },
          tags+: {
            '2i2c:node-purpose': 'user',
          },
        } + n
        for n in notebookNodes
      ] + (
        if daskNodes != null then
          [
            ng {
              namePrefix: 'dask',
              availabilityZones: [nodeAz],
              minSize: 0,
              maxSize: 500,
              labels+: {
                'k8s.dask.org/node-purpose': 'worker',
              },
              taints+: {
                'k8s.dask.org_dedicated': 'worker:NoSchedule',
                'k8s.dask.org/dedicated': 'worker:NoSchedule',
              },
              tags+: {
                '2i2c:node-purpose': 'worker',
              },
              instancesDistribution+: {
                onDemandBaseCapacity: 0,
                onDemandPercentageAboveBaseCapacity: 0,
                spotAllocationStrategy: 'capacity-optimized',
              },
            } + n
            for n in daskNodes
          ] else []
      )
  ],
}