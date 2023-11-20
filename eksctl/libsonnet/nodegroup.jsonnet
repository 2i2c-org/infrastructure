/*
  This file is imported by ../template.jsonnet and its generated files.

  Exports an object representing a node group's default fields, and is supposed
  to be merged with other objects.

  Note that the "name" output field is declared to be calculated based on hidden
  fields that objects merging into this can influence.
*/

// Exported object
{
  // If using spot instances where a Auto Scaling Group (ASG) has multiple
  // instances associated with it, label using the first instance type.
  // FIXME: Clarify the limitations of picking one of multiple instance types
  local instanceType = if 'instanceType' in $ then $.instanceType else $.instancesDistribution.instanceTypes[0],
  local escapedInstanceType = std.strReplace(instanceType, ".", "-"),

  // The cluster autoscaler reads specific tags on a Auto Scaling Group's default
  // launch template version about the k8s labels and taints that the node group
  // has in order to correctly pick the right node group to scale up. These tags
  // can't be changed.
  local caLabelTags(labels) = {
    ['k8s.io/cluster-autoscaler/node-template/label/%s' % key]: labels[key]
    for key in std.objectFields(labels)
  },
  local caTaintTags(taints) = {
    ['k8s.io/cluster-autoscaler/node-template/taint/%s' % key]: taints[key]
    for key in std.objectFields(taints)
  },
  local tags = caLabelTags(self.labels) + caTaintTags(self.taints),

  local nameParts = [self.namePrefix, self.nameBase, self.nameSuffix],

  // Hidden fields (due to ::) are used as inputs from merged objects to compute
  // output fields
  namePrefix:: "",
  nameIncludeInstanceType:: true,
  nameBase:: if self.nameIncludeInstanceType then escapedInstanceType else "",
  nameSuffix:: "",
  preventScaleUp:: false,

  // Output fields
  name: std.join("-", std.filter(function(x) x != "", nameParts)),
  availabilityZones: [],
  minSize: 0,
  desiredCapacity: self.minSize,
  volumeSize: 80,
  labels+: { 'node.kubernetes.io/instance-type': instanceType },
  taints+: {},
  tags+: tags,
  iam: {
    withAddonPolicies: {
      autoScaler: true,
    },
  },
}
