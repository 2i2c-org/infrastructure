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
        instanceType: "r5.xlarge",
        namePrefix: "nb-workshop",
        labels+: { "2i2c/hub-name": "workshop" },
        tags+: { "2i2c:hub-name": "workshop" },
    },
    {
        instanceType: "r5.xlarge",
        namePrefix: "nb-noaa-only",
        labels+: { "2i2c/hub-name": "noaa-only" },
        tags+: { "2i2c:hub-name": "noaa-only" },
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
        instanceType: "r5.4xlarge",
        namePrefix: "nb-workshop",
        labels+: { "2i2c/hub-name": "workshop" },
        tags+: { "2i2c:hub-name": "workshop" },
    },
    {
        instanceType: "r5.4xlarge",
        namePrefix: "nb-noaa-only",
        labels+: { "2i2c/hub-name": "noaa-only" },
        tags+: { "2i2c:hub-name": "noaa-only" },
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
        instanceType: "r5.16xlarge",
        namePrefix: "nb-workshop",
        labels+: { "2i2c/hub-name": "workshop" },
        tags+: { "2i2c:hub-name": "workshop" },
    },
    {
        instanceType: "r5.16xlarge",
        namePrefix: "nb-noaa-only",
        labels+: { "2i2c/hub-name": "noaa-only" },
        tags+: { "2i2c:hub-name": "noaa-only" },
    },
    {
      instanceType: "g4dn.xlarge",
      namePrefix: "gpu-staging",
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
      namePrefix: "gpu-prod",
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
    {
      instanceType: "g4dn.xlarge",
      namePrefix: "gpu-noaa-only",
      labels+: { "2i2c/hub-name": "noaa-only" },
      tags+: {
            "2i2c:hub-name": "noaa-only",
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

local daskNodes = [
    {
        namePrefix: "dask-staging",
        labels+: { "2i2c/hub-name": "staging" },
        tags+: { "2i2c:hub-name": "staging" },
        instancesDistribution+: { instanceTypes: ["r5.4xlarge"] }
    },
    {
        namePrefix: "dask-prod",
        labels+: { "2i2c/hub-name": "prod" },
        tags+: { "2i2c:hub-name": "prod" },
        instancesDistribution+: { instanceTypes: ["r5.4xlarge"] }
    },
    {
        namePrefix: "dask-workshop",
        labels+: { "2i2c/hub-name": "workshop" },
        tags+: { "2i2c:hub-name": "workshop" },
        instancesDistribution+: { instanceTypes: ["r5.4xlarge"] }
    },
    {
        namePrefix: "dask-noaa-only",
        labels+: { "2i2c/hub-name": "noaa-only" },
        tags+: { "2i2c:hub-name": "noaa-only" },
        instancesDistribution+: { instanceTypes: ["r5.4xlarge"] }
    },
];


{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "nmfs-openscapes",
        region: clusterRegion,
        version: "1.32",
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
            nameSuffix: 'b',
            nameIncludeInstanceType: false,
            availabilityZones: [nodeAz],
            ssh: {
                publicKeyPath: 'ssh-keys/nmfs-openscapes.key.pub'
            },
            instanceType: "r5.xlarge",
            minSize: 1,
            maxSize: 6,
            labels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core",
            },
            tags+: { "2i2c:node-purpose": "core" },
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
            tags+: { "2i2c:node-purpose": "user" },
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
