// Exports a customizable eksctl cluster object
// https://eksctl.io/usage/schema/ lists the config
//
// The default configuration is pretty bare, and only
// sets the default k8s version. Everything else must
// be merged in by the jsonnet file for each cluster
{
  apiVersion: 'eksctl.io/v1alpha5',
  kind: 'ClusterConfig',
  metadata: {
    name: '',
    region: '',
    version: '1.19',
  },
  availabilityZones: [],
  iam: {
    withOIDC: true,
  },
}
