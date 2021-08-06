// Exports an eksctl config file for carbonplan cluster
local cluster = import "./libsonnet/cluster.jsonnet";
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "us-west-2";
local masterAzs = ["us-west-2a", "us-west-2b", "us-west-2c"];
local nodeAz = "us-west-2a";

// Node definitions for use with dask and notebook nodes
// These are merged in with the defaults for either node type,
// and so can contain any overrides.
local nodes = [
    { instanceType: "r5.large" },
    { instanceType: "r5.xlarge" },
    { instanceType: "r5.2xlarge" },
    { instanceType: "r5.8xlarge" },
    { instanceType: "x1.16xlarge" },
    { instanceType: "x1.32xlarge" }
];

cluster {
    metadata+: {
        name: "carbonplanhub",
        region: clusterRegion
    },
    availabilityZones: masterAzs,
    nodeGroups: [
        ng {
            name: 'core-a',
            availabilityZones: [nodeAz],
            ssh: {
                publicKeyPath: 'ssh-keys/carbonplan.key.pub'
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
            name: "nb-%s" % std.strReplace(self.instanceType, ".", "-"),
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            ssh: {
                publicKeyPath: 'ssh-keys/carbonplan.key.pub'
            },
            labels+: {
                "hub.jupyter.org/node-purpose": "user",
                "k8s.dask.org/node-purpose": "scheduler"
            },
            taints+: {
                "hub.jupyter.org_dedicated": "user:NoSchedule",
                "hub.jupyter.org/dedicated": "user:NoSchedule"
            },

        } + n for n in nodes
    ] + [
        ng {
            // NodeGroup names can't have a '.' in them, while
            // instanceTypes always have a .
            name: "dask-%s" % std.strReplace(self.instanceType, ".", "-"),
            availabilityZones: [nodeAz],
            minSize: 0,
            maxSize: 500,
            ssh: {
                publicKeyPath: 'ssh-keys/carbonplan.key.pub'
            },
            labels+: {
                "k8s.dask.org/node-purpose": "worker"
            },
            taints+: {
                "k8s.dask.org_dedicated" : "worker:NoSchedule",
                "k8s.dask.org/dedicated" : "worker:NoSchedule"
            },

        } + n for n in nodes
    ]


}