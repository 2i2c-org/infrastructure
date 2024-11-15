/*
    This file is a jsonnet template of a eksctl's cluster configuration file,
    that is used with the eksctl CLI to both update and initialize an AWS EKS
    based cluster.

    This file has in turn been generated from eksctl/template.jsonnet which is
    relevant to compare with for changes over time.

    To use jsonnet to generate an eksctl configuration file from this, do:

        jsonnet catalystproject-africa.jsonnet > catalystproject-africa.eksctl.yaml

    References:
    - https://eksctl.io/usage/schema/
*/
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "af-south-1";
local masterAzs = ["af-south-1a", "af-south-1b", "af-south-1c"];
local nodeAz = "af-south-1a";

// Node definitions for notebook nodes. Config here is merged
// with our notebook node definition.
// A `node.kubernetes.io/instance-type label is added, so pods
// can request a particular kind of node with a nodeSelector
local notebookNodes = [
    // staging hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
    },
    // nm-aist hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-nm-aist",
        labels+: { "2i2c/hub-name": "nm-aist" },
        tags+: { "2i2c:hub-name": "nm-aist" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-nm-aist",
        labels+: { "2i2c/hub-name": "nm-aist" },
        tags+: { "2i2c:hub-name": "nm-aist" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-nm-aist",
        labels+: { "2i2c/hub-name": "nm-aist" },
        tags+: { "2i2c:hub-name": "nm-aist" },
    },
    // must hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-must",
        labels+: { "2i2c/hub-name": "must" },
        tags+: { "2i2c:hub-name": "must" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-must",
        labels+: { "2i2c/hub-name": "must" },
        tags+: { "2i2c:hub-name": "must" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-must",
        labels+: { "2i2c/hub-name": "must" },
        tags+: { "2i2c:hub-name": "must" },
    },
    // uvri hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-uvri",
        labels+: { "2i2c/hub-name": "uvri" },
        tags+: { "2i2c:hub-name": "uvri" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-uvri",
        labels+: { "2i2c/hub-name": "uvri" },
        tags+: { "2i2c:hub-name": "uvri" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-uvri",
        labels+: { "2i2c/hub-name": "uvri" },
        tags+: { "2i2c:hub-name": "uvri" },
    },
    // wits hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-wits",
        labels+: { "2i2c/hub-name": "wits" },
        tags+: { "2i2c:hub-name": "wits" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-wits",
        labels+: { "2i2c/hub-name": "wits" },
        tags+: { "2i2c:hub-name": "wits" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-wits",
        labels+: { "2i2c/hub-name": "wits" },
        tags+: { "2i2c:hub-name": "wits" },
    },
    // kush hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-kush",
        labels+: { "2i2c/hub-name": "kush" },
        tags+: { "2i2c:hub-name": "kush" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-kush",
        labels+: { "2i2c/hub-name": "kush" },
        tags+: { "2i2c:hub-name": "kush" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-kush",
        labels+: { "2i2c/hub-name": "kush" },
        tags+: { "2i2c:hub-name": "kush" },
    },
    // molerhealth hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-molerhealth",
        labels+: { "2i2c/hub-name": "molerhealth" },
        tags+: { "2i2c:hub-name": "molerhealth" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-molerhealth",
        labels+: { "2i2c/hub-name": "molerhealth" },
        tags+: { "2i2c:hub-name": "molerhealth" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-molerhealth",
        labels+: { "2i2c/hub-name": "molerhealth" },
        tags+: { "2i2c:hub-name": "molerhealth" },
    },
    // aibst hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-aibst",
        labels+: { "2i2c/hub-name": "aibst" },
        tags+: { "2i2c:hub-name": "aibst" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-aibst",
        labels+: { "2i2c/hub-name": "aibst" },
        tags+: { "2i2c:hub-name": "aibst" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-aibst",
        labels+: { "2i2c/hub-name": "aibst" },
        tags+: { "2i2c:hub-name": "aibst" },
    },
    // bhki hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-bhki",
        labels+: { "2i2c/hub-name": "bhki" },
        tags+: { "2i2c:hub-name": "bhki" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-bhki",
        labels+: { "2i2c/hub-name": "bhki" },
        tags+: { "2i2c:hub-name": "bhki" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-bhki",
        labels+: { "2i2c/hub-name": "bhki" },
        tags+: { "2i2c:hub-name": "bhki" },
    },
    // bon hub
    {
        instanceType: "r5.xlarge",
        volumeSize: 400,
        namePrefix: "nb-bon",
        labels+: { "2i2c/hub-name": "bon" },
        tags+: { "2i2c:hub-name": "bon" },
    },
    {
        instanceType: "r5.4xlarge",
        volumeSize: 400,
        namePrefix: "nb-bon",
        labels+: { "2i2c/hub-name": "bon" },
        tags+: { "2i2c:hub-name": "bon" },
    },
    {
        instanceType: "r5.16xlarge",
        volumeSize: 400,
        namePrefix: "nb-bon",
        labels+: { "2i2c/hub-name": "bon" },
        tags+: { "2i2c:hub-name": "bon" },
    },
];
local daskNodes = [];


{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "catalystproject-africa",
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
    //    eksctl create addon --config-file=catalystproject-africa.eksctl.yaml
    //
    addons: [
        { version: "latest", tags: $.metadata.tags } + addon
        for addon in
        [
            { name: "coredns" },
            { name: "kube-proxy" },
            {
                // vpc-cni is a Amazon maintained container networking interface
                // (CNI), where a CNI is required for k8s networking. The aws-node
                // DaemonSet in kube-system stems from installing this.
                //
                // Related docs: https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/
                //               https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html
                //
                name: "vpc-cni",
                attachPolicyARNs: ["arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"],
                # FIXME: enabling network policy enforcement didn't work as of
                #        August 2024, what's wrong isn't clear.
                #
                # configurationValues ref: https://github.com/aws/amazon-vpc-cni-k8s/blob/HEAD/charts/aws-vpc-cni/values.yaml
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
                publicKeyPath: 'ssh-keys/catalystproject-africa.key.pub'
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
            namePrefix: "nb",
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            instanceType: n.instanceType,
            ssh: {
                publicKeyPath: 'ssh-keys/catalystproject-africa.key.pub'
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
            namePrefix: "dask",
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            ssh: {
                publicKeyPath: 'ssh-keys/catalystproject-africa.key.pub'
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
