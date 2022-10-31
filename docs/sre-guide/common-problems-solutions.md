(troubleshooting)=
# Common problems and their solutions

These sections describe a few common problems we face on our infrastructure and tips on how to solve them.

```{contents}
:local:
```

(troubleshooting/rollback)=
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

(troubleshooting/prometheus-oom)=
## Prometheus server is out of memory (OOM)

Prometheus collects Kubernetes metrics for our grafana charts and often requires a lot of memory during startup.
If the server runs out of memory during the startup process, this presents itself as a "Timed out waiting for condition" error from `helm` on the command line, and `OOMKilled` events in the prometheus server pod events before the pod reverts to `CrashLoopBackOff` status.
This might also block our CI/CD system from updating the hubs on the cluster if the support chart requires an upgrade after a Pull Request is merged.

To resolve this issue, we feed prometheus more RAM which you can do by adding the below config to the `support.values.yaml` file under the relevant folder in `config/clusters`.

```yaml
prometheus:
  server:
    resources:
      limits:
        memory: {{RAM_LIMIT}}
```

The [default for this value is 2GB](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/support/values.yaml#L38).
Try increasing this value in small increments and deploying using `python deployer deploy-support {{CLUSTER_NAME}}` until the server successfully starts up.
Then make a Pull Request with your updated config.

(troubleshooting/validation-webhook)=
## Failure calling validation webhook for `support` components

After addressing [](troubleshooting/prometheus-oom), you may see the following error when redeploying the support chart:

```bash
Error: UPGRADE FAILED: cannot patch "support-prometheus-server" with kind Ingress: Internal error occurred: failed calling webhook "validate.nginx.ingress.kubernetes.io": Post "https://support-ingress-nginx-controller-admission.support.svc:443/networking/v1beta1/ingresses?timeout=10s": x509: certificate signed by unknown authority
```

You can resolve this by deleting the webhook and redeploying - helm will simply recreate the webhook.

```bash
kubectl -A delete ValidatingWebhookConfiguration support-ingress-nginx-admission
```

where the `-A` flag will apply this command across all namespaces.

````{tip}
Find the webhooks running on a cluster by running:

```bash
kubectl -A get ValidatingWebhooksConfigurations
```
````
