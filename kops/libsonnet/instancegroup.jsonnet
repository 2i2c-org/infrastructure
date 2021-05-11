
local makeCloudLabels(labels) = {
        ["k8s.io/cluster-autoscaler/node-template/label/%s" % key]: labels[key]
        for key in std.objectFields(labels)
};
// Kops expects these as strings of form Key=Value:Effect in spec.taints,
// but cloudlabels expects them to be key value pairs of Key: Value:Effect
local makeCloudTaints(taints) = {
    ["k8s.io/cluster-autoscaler/node-template/taint/%s" % splits[0]]: splits[1]
    for splits in [std.split(t, '=') for t in taints]
};


// local instanceGroup(name, clusterName, nodeImage, labels, taints, machineType, subnets, minSize, maxSize, role) = {
{
    _config+:: {
        clusterName: ""
    },
    apiVersion: "kops.k8s.io/v1alpha2",
    kind: "InstanceGroup",
    metadata: {
        labels+: {
            "kops.k8s.io/cluster": $._config.clusterName,
        },
        name: ""
    },
    spec: {
        image: "099720109477/ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20210119.1",
        cloudLabels: {
            // Tell autoscaler to scale up this instancegroup when something asks for a node with the label
            // node.kubernetes.io/instance-type: <machineType>
            "k8s.io/cluster-autoscaler/node-template/label/node.kubernetes.io/instance-type": $.spec.machineType
        } + makeCloudLabels(self.nodeLabels) + makeCloudTaints(self.taints),
        taints: [],
        nodeLabels: {},
        machineType: "",
        maxSize: 20,
        minSize: 0,
        role: "Master",
        subnets: [],
    }
}