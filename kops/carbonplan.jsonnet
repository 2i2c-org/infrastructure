local cluster = import "./libsonnet/cluster.jsonnet";
local ig = import "./libsonnet/instancegroup.jsonnet";

local zone = "us-east-1a";
local nodes = [
    {spec+: {
        machineType: "m4.xlarge"
    }},
    {spec+: {
        machineType: "m4.2xlarge",
        maxSize: 20
    }},
];

local data = {
    cluster: cluster {
        metadata+: {
            name: "farallon.k8s.local"
        },
        spec+: {
            configBase: "hi"
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
                maxSize: 3,
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