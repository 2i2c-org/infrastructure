# Troubleshooting and debugging

These sections describe a few common and useful tips for troubleshooting our infrastructure.

## Roll back (revert) a helm deploy

Sometimes it is useful to simply **revert** a Kubernetes deployment with Helm.
For example, if you've manually deployed something via `helm upgrade`, and notice that something is wrong with our deployment.

:::{note}
Ideally, this would have happened automatically via CI/CD, but sometimes a manual deploy is still necessary!
:::

If you'd simply like to revert back to the state of the Kubernetes infrastructure from before you ran `helm install`, try the following commands:

- **Get the deployment name and revision number for the latest deploy**. To do so, run this command:

  ```bash
  helm list --namespace {{NAMESPACE}}
  ```

- Roll back the deployment to the previous revision, using the information output from the above command:

  ```bash
  helm rollback --namespace {{NAMESPACE}} {{DEPLOYMENT_NAME}} {{REV_NUM - 1}}
  ```

  The {{REV_NUM - 1}} simply means "deploy the previous revision number".
  Usually, `NAMESPACE` and `DEPLOYMENT_NAME` are identical, but always best to double check.

This should revert the Helm deployment to the previous revision (the one just before you ran `helm upgrade`).

## Prometheus Server is Out Of Memory (OOM)

Prometheus collects Kubernetes metrics for our grafana charts and often requires a lot of memory during startup.
If the server runs out of memory during the startup process, this presents itself as a "Timed out waiting for condition" error from `helm` on the command line, and `OOMKilled` events in the prometheus server pod events before the pod reverts to `CrashLoopBackOff` status.
This will also block our CI/CD system from updating the hubs on the cluster since the support chart is always upgraded before the hub charts.

To resolve this issue, we feed prometheus more RAM which you can do by adding the below config to the relevant `*.cluster.yaml` file.

```yaml
support:
  config:
    prometheus:
      server:
        resources:
          limits:
            memory: {{RAM_LIMIT}}
```

The [default for this value is 2GB](https://github.com/2i2c-org/infrastructure/blob/dfe32345dc0b7d7cb961d6721bca291ab853e04b/support/values.yaml#L38).
Try increasing this value in small increments and deploying using `python deployer deploy-support {{CLUSTER_NAME}}` until the server successfully starts up.
Then make a Pull Request with your updated config.
