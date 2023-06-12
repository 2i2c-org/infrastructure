(prometheus)=
# Prometheus

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to
collect metrics and information about activity on the hub

The prometheus server runs in the support namespace.

(prometheus:access-prometheus)=
## Logging in

Kubernetes port forwarding can be used to access the prometheus dashboard which
can be used to check scrape targets and the metrics explorer to examine
available metrics.

```
deployer use-cluster-credentials $CLUSTER
kubectl port-forward -n support deploy/support-prometheus-server 9090:9090
```
