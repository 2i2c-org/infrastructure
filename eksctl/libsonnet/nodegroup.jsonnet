// This file is referenced by ../template.jsonnet. It declares an object
// representing a node group that is used as a common foundation for all
// our node groups.
//

// Make Auto Scaling Group (ASG) tags for given set of k8s labels
local makeCloudLabels(labels) = {
  ['k8s.io/cluster-autoscaler/node-template/label/%s' % key]: labels[key]
  for key in std.objectFields(labels)
};

# Make ASG tags for given set of k8s taints
local makeCloudTaints(taints) = {
  ['k8s.io/cluster-autoscaler/node-template/taint/%s' % key]: taints[key]
  for key in std.objectFields(taints)
};

{
  name: '',
  availabilityZones: [],
  minSize: 0,
  desiredCapacity: self.minSize,
  volumeSize: 80,
  labels+: {
	  // Add instance type as label to nodegroups, so they
    // can be picked up by the autoscaler. If using spot instances,
    // pick the first instancetype
    'node.kubernetes.io/instance-type': if std.objectHas($, 'instanceType') then $.instanceType else $.instancesDistribution.instanceTypes[0],
  },
  taints+: {},
  tags+: makeCloudLabels(self.labels) + makeCloudTaints(self.taints),
  iam: {
    withAddonPolicies: {
      autoScaler: true,
    },
  },
}
