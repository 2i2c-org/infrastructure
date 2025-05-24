/*
  This file is imported by ../template.jsonnet and its generated files.

  Exports an object representing a node group's default fields, and is supposed
  to be merged with other objects.

  Note that the "name" output field is declared to be calculated based on hidden
  fields that objects merging into this can influence.
*/

// Exported object
{
  // Note that spot instances configured via an Auto Scaling Group (ASG) can have
  // multiple instance types associated with it (with the same CPU/RAM/GPU), we
  // label them using the first instance type in the ASG as a compromise.
  //
  // More details at:
  // https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md#using-mixed-instances-policies-and-spot-instances
  //
  local instanceType = if 'instanceType' in $ then $.instanceType else $.instancesDistribution.instanceTypes[0],
  // NodeGroup names can't have a '.' in them as instanceTypes has
  local escapedInstanceType = std.strReplace(instanceType, '.', '-'),

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
  local commonTags = {
    ManagedBy: '2i2c',
    '2i2c.org/cluster-name': $.clusterName,
  },
  local tags = caLabelTags(self.labels) + caTaintTags(self.taints) + commonTags,

  local nameParts = [self.namePrefix, self.nameBase, self.nameSuffix],

  // Hidden fields (due to ::) are used as inputs from merged objects to compute
  // output fields
  clusterName:: '',
  namePrefix:: '',
  nameIncludeInstanceType:: true,
  nameBase:: if self.nameIncludeInstanceType then escapedInstanceType else '',
  nameSuffix:: '',
  preventScaleUp:: false,

  // Output fields
  name: std.join('-', std.filter(function(x) x != '', nameParts)),
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
