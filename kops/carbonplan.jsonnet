local cluster = import "./libsonnet/cluster.jsonnet";
local ig = import "./libsonnet/instancegroup.jsonnet";

local zone = "us-west-2a";
local nodes = [
    {spec+: { machineType: "r5.large" }}, // 2CPU, 16G RAM
    {spec+: { machineType: "r5.xlarge" }}, // 4CPU, 32G RAM
    {spec+: { machineType: "r5.2xlarge" }}, // 8CPU, 64G RAM
    {spec+: { machineType: "r5.8xlarge" }} // 32CPU, 256 RAM
];

local data = {
    cluster: cluster {
        metadata+: {
            name: "carbonplanhub.k8s.local"
        },
        spec+: {
            configBase: "s3://2i2c-carbonplan-kops-state"
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
            machineType: "t3.medium",
            subnets: [zone],
            nodeLabels+: {
                "hub.jupyter.org/pool-name": "core-pool"
            },
            // Needs to be at least 1
            minSize: 1,
            maxSize: 3,
            role: "Master"
        },
    },
    nodes: [
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
                    "hub.jupyter.org/pool-name": thisIg.metadata.name
                },
                taints: [
                    "hub.jupyter.org_dedicated=user:NoSchedule",
                    "hub.jupyter.org/dedicated=user:NoSchedule"
                ],
            },
        } + n for n in nodes
    ]
};

[
    data.cluster,
    data.master
] + data.nodes