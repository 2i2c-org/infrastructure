{#-
    This file is a jinja2 template of a jsonnet template of a eksctl's cluster
    configuration file, which in turn is to be used with the eksctl CLI to both
    update and initialize an AWS EKS based cluster.

    This jinja2 template is used by the deployer script's generate-aws-cluster
    command as part of creating new clusters.

    References:
    - https://infrastructure.2i2c.org/en/latest/hub-deployment-guide/new-cluster/aws.html#generate-cluster-files
-#}
/*
    This file is a jsonnet template of a eksctl's cluster configuration file,
    that is used with the eksctl CLI to both update and initialize an AWS EKS
    based cluster.

    This file has in turn been generated from eksctl/template.jsonnet which is
    relevant to compare with for changes over time.

    To use jsonnet to generate an eksctl configuration file from this, do:

        jsonnet << cluster_name >>.jsonnet > << cluster_name >>.eksctl.yaml

    References:
    - https://eksctl.io/usage/schema/
*/
local ng = import "./libsonnet/nodegroup.jsonnet";

// place all cluster nodes here
local clusterRegion = "<< cluster_region >>";
local masterAzs = ["<< cluster_region >>a", "<< cluster_region >>b", "<< cluster_region >>c"];
local nodeAz = "<< cluster_region >>a";

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
<% if hub_type == "daskhub" %>
local daskNodes = [
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
<% else %>
local daskNodes = [];
<% endif %>


{
    apiVersion: 'eksctl.io/v1alpha5',
    kind: 'ClusterConfig',
    metadata+: {
        name: "<< cluster_name >>",
        region: clusterRegion,
        version: '1.24'
    },
    availabilityZones: masterAzs,
    iam: {
        withOIDC: true,
    },
    // If you add an addon to this config, run the create addon command.
    //
    //    eksctl create addon --config-file=<< cluster_name >>.eksctl.yaml
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
            wellKnownPolicies: {
                ebsCSIController: true,
            },
        },
    ],
    nodeGroups: [
        ng {
            name: 'core-a',
            availabilityZones: [nodeAz],
            ssh: {
                publicKeyPath: 'ssh-keys/<< cluster_name >>.key.pub'
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
                publicKeyPath: 'ssh-keys/<< cluster_name >>.key.pub'
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
                publicKeyPath: 'ssh-keys/<< cluster_name >>.key.pub'
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
