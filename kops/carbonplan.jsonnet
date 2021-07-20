local cluster = import "./libsonnet/cluster.jsonnet";
local ig = import "./libsonnet/instancegroup.jsonnet";

local zone = "us-west-2a";
local nodes = [
    {spec+: { machineType: "r5.large" }}, // 2CPU, 16G RAM
    {spec+: { machineType: "r5.xlarge" }}, // 4CPU, 32G RAM
    {spec+: { machineType: "r5.2xlarge" }}, // 8CPU, 64G RAM
    {spec+: { machineType: "r5.8xlarge" }}, // 32CPU, 256 RAM
    {spec+: { machineType: "x1.16xlarge" }}, // 64CPU, 976G RAM
    {spec+: { machineType: "x1.32xlarge" }} // 128CPU, 1952G RAM
];

local data = {
    cluster: cluster {
        metadata+: {
            name: "carbonplanhub.k8s.local"
        },
        spec+: {
            // FIXME: Not sure if this is necessary?
            configBase: "s3://2i2c-carbonplan-kops-state/%s" % data.cluster.metadata.name,

            etcdClusters: [
                {
                    cpuRequest: "500m",
                    etcdMembers: [
                        {
                            instanceGroup: "master",
                            name: "a"
                        },
                        {
                            instanceGroup: "master",
                            name: "b"
                        },
                        {
                            instanceGroup: "master",
                            name: "c"
                        }
                    ],
                    memoryRequest: "1Gi",
                    name: "main"
                },
                {
                    cpuRequest: "500m",
                    etcdMembers: [

                        {
                            instanceGroup: "master",
                            name: "a"
                        },
                        {
                            instanceGroup: "master",
                            name: "b"
                        },
                        {
                            instanceGroup: "master",
                            name: "c"
                        }
                    ],
                    memoryRequest: "1Gi",
                    name: "events"
                }
            ],
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
            machineType: "m5.4xlarge",
            subnets: [zone],
            // CarbonPlan runs big jobs, so let's have a big node here
            minSize: 1,
            maxSize: 3,
            role: "Master"
        },
    },
    coreNodes: ig {
        metadata+: {
            labels+: {
                "kops.k8s.io/cluster": data.cluster.metadata.name
            },
            name: "core"
        },
        spec+: {
            machineType: "m5.xlarge",
            subnets: [zone],
            nodeLabels+: {
                "hub.jupyter.org/node-purpose": "core",
                "k8s.dask.org/node-purpose": "core"
            },
            minSize: 2,
            maxSize: 6,
            role: "Node"
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
                maxSize: 500,
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
                maxSize: 500,
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
    data.master,
    data.coreNodes
] + data.notebookNodes + data.daskNodes