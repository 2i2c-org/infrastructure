// Make ASG tags for given set of k8s labels
local makeCloudLabels(labels) = {
  ['k8s.io/cluster-autoscaler/node-template/label/%s' % key]: labels[key]
  for key in std.objectFields(labels)
};

# Make asg tags for given set of k8s taints
local makeCloudTaints(taints) = {
  ['k8s.io/cluster-autoscaler/node-template/taint/%s' % key]: taints[key]
  for key in std.objectFields(taints)
};

{
  name: '',
  availabilityZones: [],
  minSize: 0,
  desiredCapacity: self.minSize,
  instanceType: '',
  volumeSize: 80,
  labels+: {
	  // Add instance type as label to nodegroups, so they
	  // can be picked up by the autoscaler
    'node.kubernetes.io/instance-type': $.instanceType,
  },
  taints+: {},
  tags: makeCloudLabels(self.labels) + makeCloudTaints(self.taints),
  iam: {
    withAddonPolicies: {
      autoScaler: true,
    },
  },
}
