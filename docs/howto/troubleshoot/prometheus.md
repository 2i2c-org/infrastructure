# Troubleshoot prometheus issues

We use prometheus data exposed via grafana to troubleshoot a lot of other
issues, but sometimes prometheus itself can have issues and not start.
This page documents various issues that might be causing that, and how
to address them.

## Running out of disk space

If there are enough metrics retained for long enough, prometheus will
run out of disk space and not record any more metrics. Increasing the
size of the disk will fix this issue. The default is set in
`helm-charts/support/values.yaml` to `100Gi`, but can be increased
for a specific cluster in its `support.values.yaml` file:

```yaml
prometheus:
  server:
    persistentVolume:
      # 100Gi was too little
      size: 200Gi
```

Doing a deploy after this should be sufficient, as Kubernetes will
[dynamically resize the volume](https://kubernetes.io/blog/2018/07/12/resizing-persistent-volumes-using-kubernetes/)
