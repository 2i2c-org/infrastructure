/*
    This file is a jsonnet template of a eksctl's cluster configuration file,
    that is used with the eksctl CLI to both update and initialize an AWS EKS
    based cluster.

    This file has in turn been generated from eksctl/template.jsonnet which is
    relevant to compare with for changes over time.

    To use jsonnet to generate an eksctl configuration file from this, do:

        jsonnet kitware.jsonnet > kitware.eksctl.yaml

    References:
    - https://eksctl.io/usage/schema/
*/
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "us-west-2";
local masterAzs = ["us-west-2a", "us-west-2b", "us-west-2c"];
local nodeAz = "us-west-2a";

// Node definitions for notebook nodes. Config here is merged
// with our notebook node definition.
// A `node.kubernetes.io/instance-type label is added, so pods
// can request a particular kind of node with a nodeSelector
local notebookNodes = [
    {
        instanceType: "r5.xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r5.xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
    {
        instanceType: "r5.4xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r5.4xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
    {
        instanceType: "r5.16xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r5.16xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
    {
      instanceType: "g4dn.xlarge",
      namePrefix: "nb-staging",
      labels+: { "2i2c/hub-name": "staging" },
      tags+: {
        "2i2c:hub-name": "staging",
        "k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu": "1"
      },
      taints+: {
          "nvidia.com/gpu": "present:NoSchedule"
      },
      // Allow provisioning GPUs across all AZs, to prevent situation where all
      // GPUs in a single AZ are in use and no new nodes can be spawned
      availabilityZones: masterAzs,
    },
    {
      instanceType: "g4dn.xlarge",
      namePrefix: "nb-prod",
      labels+: { "2i2c/hub-name": "prod" },
      tags+: {
        "2i2c:hub-name": "prod",
        "k8s.io/cluster-autoscaler/node-template/resources/nvidia.com/gpu": "1"
      },
      taints+: {
          "nvidia.com/gpu": "present:NoSchedule"
      },
      // Allow provisioning GPUs across all AZs, to prevent situation where all
      // GPUs in a single AZ are in use and no new nodes can be spawned
      availabilityZones: masterAzs,
    },
];
local daskNodes = [];


{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "kitware",
        region: clusterRegion,
        version: "1.30",
    },
    availabilityZones: masterAzs,
    iam: {
        withOIDC: true,
    },
    // If you add an addon to this config, run the create addon command.
    //
    //    eksctl create addon --config-file=kitware.eksctl.yaml
    //
    addons: [
        {
            // aws-ebs-csi-driver ensures that our PVCs are bound to PVs that
            // couple to AWS EBS based storage, without it expect to see pods
            // mounting a PVC failing to schedule and PVC resources that are
            // unbound.
            //
            // Related docs: https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html
            //
            name: 'aws-ebs-csi-driver',
            version: "latest",
            wellKnownPolicies: {
                ebsCSIController: true,
            },
        },
    ],
    nodeGroups: [
    n + {clusterName: $.metadata.name} for n in
    [
        ng + {
            namePrefix: 'core',
            nameSuffix: 'a',
            nameIncludeInstanceType: false,
            availabilityZones: [nodeAz],
            ssh: {
                publicKeyPath: 'ssh-keys/kitware.key.pub'
            },
            instanceType: "r5.xlarge",
            minSize: 1,
            maxSize: 6,
            labels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core"
            },
        },
    ] + [
        ng + {
            namePrefix: 'nb',
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            instanceType: n.instanceType,
            ssh: {
                publicKeyPath: 'ssh-keys/kitware.key.pub'
            },
            labels+: {
                "hub.jupyter.org/node-purpose": "user",
                "k8s.dask.org/node-purpose": "scheduler"
            },
            taints+: {
                "hub.jupyter.org_dedicated": "user:NoSchedule",
                "hub.jupyter.org/dedicated": "user:NoSchedule"
            },
        } + n for n in notebookNodes
    ] + ( if daskNodes != null then
        [
        ng + {
            namePrefix: 'dask',
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            ssh: {
                publicKeyPath: 'ssh-keys/kitware.key.pub'
            },
            labels+: {
                "k8s.dask.org/node-purpose": "worker"
            },
            taints+: {
                "k8s.dask.org_dedicated" : "worker:NoSchedule",
                "k8s.dask.org/dedicated" : "worker:NoSchedule"
            },
            instancesDistribution+: {
                onDemandBaseCapacity: 0,
                onDemandPercentageAboveBaseCapacity: 0,
                spotAllocationStrategy: "capacity-optimized",
            },
        } + n for n in daskNodes
        ] else []
    )
    ]
}
