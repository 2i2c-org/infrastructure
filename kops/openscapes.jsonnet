local cluster = import "./libsonnet/cluster.jsonnet";
local ig = import "./libsonnet/instancegroup.jsonnet";

local zone = "us-west-2b";
local nodes = [
    {spec+: { machineType: "m5.large" }}, // 2CPU, 8G RAM
    {spec+: { machineType: "m5.xlarge" }}, // 4CPU, 16G RAM
    {spec+: { machineType: "m5.2xlarge" }}, // 8CPU, 32G RAM
    {spec+: { machineType: "m5.8xlarge" }} // 32CPU, 128G RAM
];

local data = {
    cluster: cluster {
        metadata+: {
            name: "openscapeshub.k8s.local"
        },
        _config+:: {
            zone: zone,
            masterInstanceGroupName: data.master.metadata.name
        }
    },
    master: ig {
        metadata+: {
            labels+: {
                "kops.k8s.io/cluster": data.cluster.metadata.name
            },
            name: "master"
        },
        spec+: {
            machineType: "m5.medium",
            subnets: [zone],
            nodeLabels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core"
            },
            // Needs to be at least 1
            minSize: 1,
            maxSize: 3,
            role: "Master"
        },
    },
    notebookNodes: [
        ig {
            local thisIg = self,
            metadata+: {
                labels+: {
                    "kops.k8s.io/cluster": data.cluster.metadata.name
                },
                name: "notebook-%s" % std.strReplace(thisIg.spec.machineType, ".", "-")
            },
            spec+: {
                machineType: n.machineType,
                subnets: [zone],
                maxSize: 20,
                role: "Node",
                nodeLabels+: {
                    "hub.jupyter.org/node-purpose": "user",
                    "k8s.dask.org/node-purpose": "scheduler"
                },
                taints: [
                    "hub.jupyter.org_dedicated=user:NoSchedule",
                    "hub.jupyter.org/dedicated=user:NoSchedule"
                ],
            },
        } + n for n in nodes
    ],
    daskNodes: [
        ig {
            local thisIg = self,
            metadata+: {
                labels+: {
                    "kops.k8s.io/cluster": data.cluster.metadata.name
                },
                name: "dask-%s" % std.strReplace(thisIg.spec.machineType, ".", "-")
            },
            spec+: {
                machineType: n.machineType,
                subnets: [zone],
                maxSize: 20,
                role: "Node",
                nodeLabels+: {
                    "k8s.dask.org/node-purpose": "worker"
                },
                taints: [
                    "k8s.dask.org_dedicated=worker:NoSchedule",
                    "k8s.dask.org/dedicated=worker:NoSchedule"
                ],
            },
        } + n for n in nodes
    ]
};

[
    data.cluster,
    data.master
] + data.notebookNodes + data.daskNodes