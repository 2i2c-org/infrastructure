// Exports an eksctl config file for carbonplan cluster
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "ca-central-1";
local masterAzs = ["ca-central-1a", "ca-central-1b", "ca-central-1d"];
local nodeAz = "ca-central-1a";

// Node definitions for notebook nodes. Config here is merged
// with our notebook node definition.
// A `node.kubernetes.io/instance-type label is added, so pods
// can request a particular kind of node with a nodeSelector
local notebookNodes = [
    { instanceType: "m5.large" },
    { instanceType: "m5.xlarge" },
    { instanceType: "m5.2xlarge" },
    { instanceType: "m5.8xlarge" },
];

local daskNodes =
    if "basehub" == "daskhub" then [
    // Node definitions for dask worker nodes. Config here is merged
    // with our dask worker node definition, which uses spot instances.
    // A `node.kubernetes.io/instance-type label is set to the name of the
    // *first* item in instanceDistribution.instanceTypes, to match
    // what we do with notebook nodes. Pods can request a particular
    // kind of node with a nodeSelector
        { instancesDistribution+: { instanceTypes: ["m5.large"] }},
        { instancesDistribution+: { instanceTypes: ["m5.xlarge"] }},
        { instancesDistribution+: { instanceTypes: ["m5.2xlarge"] }},
        { instancesDistribution+: { instanceTypes: ["m5.8xlarge"] }},
    ];
{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "ubc-eoas",
        region: clusterRegion,
        version: '1.24'
    },
    availabilityZones: masterAzs,
    iam: {
        withOIDC: true,
    },
    nodeGroups: [
        ng {
            name: 'core-a',
            availabilityZones: [nodeAz],
            ssh: {
                publicKeyPath: 'ssh-keys/ubc-eoas.key.pub'
            },
            instanceType: "m5.xlarge",
            minSize: 1,
            maxSize: 6,
            labels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core"
            },
        },
    ] + [
        ng {
            // NodeGroup names can't have a '.' in them, while
            // instanceTypes always have a .
            name: "nb-%s" % std.strReplace(n.instanceType, ".", "-"),
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            instanceType: n.instanceType,
            ssh: {
                publicKeyPath: 'ssh-keys/ubc-eoas.key.pub'
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
        ng {
            // NodeGroup names can't have a '.' in them, while
            // instanceTypes always have a .
            name: "dask-%s" % std.strReplace(n.instancesDistribution.instanceTypes[0], ".", "-"),
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            ssh: {
                publicKeyPath: 'ssh-keys/ubc-eoas.key.pub'
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
}