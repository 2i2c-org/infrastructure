local cluster = import './libsonnet/cluster.jsonnet';

local c = cluster.withNodeGroupConfigOverride(
  cluster.withNodeGroupConfigOverride(
    cluster.withNodeGroupConfigOverride(
      cluster.makeCluster(
        name='earthscope',
        region='us-east-2',
        nodeAz='us-east-2a',
        version='1.34',
        coreNodeInstanceType='r8i-flex.large',
        notebookCPUInstanceTypes=[
          'r5.xlarge',
          'r5.4xlarge',
          'r5.16xlarge',
        ],
        daskInstanceTypes=[
          // Allow for a range of spot instance types
          [
            'r5.xlarge',
            'r6i.xlarge',
            'r7i.xlarge',
            'r8i.xlarge',
            'r8i-flex.xlarge',
          ],
        ],
        hubs=['staging', 'prod', 'binder'],
        notebookGPUNodeGroups=[
          {
            instanceType: 'g4dn.xlarge',
          },
        ],
        nodeGroupGenerations=['b', 'd']
      ),
      // Add provenence of resources
      overrides={
        tags+: {
          'earthscope:application:name': 'geolab',
          'earthscope:application:owner': 'research-onramp-to-the-cloud',
        },
      }
    ),
    kind='notebook',
    overrides={
      // 80 GiB reserved + 4*20GiB (four users)
      volumeSize: 160,
      // Ensure that /tmp is faster
      volumeIOPS: 3000,
      volumeThroughput: 500,
    }
  )
);
c
