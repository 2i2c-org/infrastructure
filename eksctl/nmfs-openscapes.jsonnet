/*
    This file is a jsonnet template of a eksctl's cluster configuration file,
    that is used with the eksctl CLI to both update and initialize an AWS EKS
    based cluster.

    This file has in turn been generated from eksctl/template.jsonnet which is
    relevant to compare with for changes over time.

    To use jsonnet to generate an eksctl configuration file from this, do:

        jsonnet nmfs-openscapes.jsonnet > nmfs-openscapes.eksctl.yaml

    References:
    - https://eksctl.io/usage/schema/
*/
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "us-west-2";
local masterAzs = ["us-west-2a", "us-west-2b", "us-west-2c"];
local nodeAz = "us-west-2b";

// Node definitions for notebook nodes. Config here is merged
// with our notebook node definition.
// A `node.kubernetes.io/instance-type label is added, so pods
// can request a particular kind of node with a nodeSelector
local notebookNodes = [
    {
        instanceType: "r7i.xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c.org/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r7i.4xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c.org/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r7i.16xlarge",
        namePrefix: "nb-staging",
        labels+: { "2i2c.org/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r7i.xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c.org/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
    {
        instanceType: "r7i.4xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c.org/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
    {
        instanceType: "r7i.16xlarge",
        namePrefix: "nb-prod",
        labels+: { "2i2c.org/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
    },
];
local daskNodes = [];


{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "nmfs-openscapes",
        region: clusterRegion,
        version: "1.30",
        tags+: {
            "ManagedBy": "2i2c",
            "2i2c.org/cluster-name": $.metadata.name,
        },
    },
    availabilityZones: masterAzs,
    iam: {
        withOIDC: true,
    },
    // If you add an addon to this config, run the create addon command.
    //
    //    eksctl create addon --config-file=nmfs-openscapes.eksctl.yaml
    //
    addons: [
        { version: "latest", tags: $.metadata.tags } + addon
        for addon in
        [
            {
                name: "vpc-cni",
                # configurationValues ref: https://github.com/aws/amazon-vpc-cni-k8s/blob/HEAD/charts/aws-vpc-cni/values.yaml
                configurationValues: |||
                    enableNetworkPolicy: "true"
                |||,
            },
            { name: "coredns" },
            { name: "kube-proxy" },
            {
                // aws-ebs-csi-driver ensures that our PVCs are bound to PVs that
                // couple to AWS EBS based storage, without it expect to see pods
                // mounting a PVC failing to schedule and PVC resources that are
                // unbound.
                //
                // Related docs: https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html
                //
                name: "aws-ebs-csi-driver",
                wellKnownPolicies: {
                    ebsCSIController: true,
                },
                # configurationValues ref: https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/HEAD/charts/aws-ebs-csi-driver/values.yaml
                configurationValues: |||
                    defaultStorageClass:
                        enabled: true
                |||,
            },
        ]
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
                publicKeyPath: 'ssh-keys/nmfs-openscapes.key.pub'
            },
            instanceType: "r7i.xlarge",
            minSize: 1,
            maxSize: 6,
            labels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core",
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
                publicKeyPath: 'ssh-keys/nmfs-openscapes.key.pub'
            },
            labels+: {
                "hub.jupyter.org/node-purpose": "user",
                "k8s.dask.org/node-purpose": "scheduler"
            },
            taints+: {
                "hub.jupyter.org_dedicated": "user:NoSchedule",
                "hub.jupyter.org/dedicated": "user:NoSchedule",
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
                publicKeyPath: 'ssh-keys/nmfs-openscapes.key.pub'
            },
            labels+: {
                "k8s.dask.org/node-purpose": "worker"
            },
            taints+: {
                "k8s.dask.org_dedicated" : "worker:NoSchedule",
                "k8s.dask.org/dedicated" : "worker:NoSchedule",
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