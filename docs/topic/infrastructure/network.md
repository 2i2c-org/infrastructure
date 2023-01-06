# Network policy

2i2c-managed hubs have a permissive network policy for the user servers that allows all outbound access to the internet, but restricts traffic within the cluster.

The policy is [defined in the `basehub` chart](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L153) and is inherited by the `daskhub` chart.
