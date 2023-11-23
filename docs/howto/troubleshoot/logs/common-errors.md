# Common errors and what logs to check

Based on the errors experienced, specific logs can have more information about the underlying issue.

## 5xx errors during login or server start

These kind of errors are reported by the hub, so checking the [hub pod logs](howto-troubleshoot:hub-pod-logs) might provide more insight on why they are happening.

## Scaling issues

If any scaling-related errors are reported, then the first thing to check is the cluster `autoscaler` logs from the [cloud console](howto-troubleshoot:gcp-autoscaler-logs) or through [kubectl](howto-troubleshoot:kubectl-autoscaler-logs).

### Dask issues

If users are experiencing issues related to Dask, then:
- something might be going on with `dask-gateway` and the logs of the pods related with this service might have more useful info.
  You can look at dask-gateway logs either with [kubectl](howto-troubleshoot:kubectl-dask-gateway-logs) or [from the cloud console](howto-troubleshoot:gcloud-dask-gateway-logs).
- there might be some connectivity issue and the traefik logs might help.
  Traefik pod logs are available from `kubectl` using the commands described in [this troubleshooting section](howto-troubleshoot:kubectl-traefik-logs).