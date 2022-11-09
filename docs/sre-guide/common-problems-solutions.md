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
Try increasing this value in small increments and deploying using `deployer deploy-support {{CLUSTER_NAME}}` until the server successfully starts up.
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

## `No space left on device` error

If users report a `No space left on device` error message when trying to login or
use an `nbgitpuller` link, this is because the NFS mount storing users home
directories is full. We rectify this by increasing the size of the NFS store.

```{note}
AWS EFS scales infinitely automatically, so we shouldn't see this error on AWS-hosted hubs.
```

### GCP Filestore

1. Navigate to <https://console.cloud.google.com/filestore/instances> and ensure the correct Google Cloud project is selected in the top menu bar
2. Select the Filestore you wish to resize from the list
3. Click the "Edit" button at the top of the page
4. Add the new capacity in the "Edit capacity" field. The value is Terabytes (TiB).
5. Click "Save". Once this update has precipitated, users should now be able to login again.
6. Follow-up this workflow with a PR to the infrastructure repo that updates the size of the Filestore in the appropriate `.tfvars` file (under `terraform/gcp/projects`) to match the change made in the console

```{important}
It is critical to complete this workflow by opening a PR, otherwise the changes
made in the console will be undone the next time we run terraform!
```

### Manual NFS deployment to a VM on GCP

```{warning}
We have deprecated this method of deploying the NFS store but some of our clusters
still use it presently.
```

1. Navigate to <https://console.cloud.google.com/compute/disks> and ensure the correct Google Cloud project is selected in the top menu bar
2. Select the disk named `hub-homes-01`. The "Details" page should show "In use by: `nfs-server-01`".
3. Click the "Edit" button at the top of the page
4. Add the new disk size in the "Size" field under "Properties". The value is Gigabytes (GB).
5. Click "Save"
6. Navigate to the NFS VM that has the disk you just edited mounted to it. You can quickly get there by clicking `nfs-server-01` in the "In use by" field on the "Details" page of the disk.
7. SSH into this VM. There is a dropdown menu called "SSH" at the top of the page that provides a variety of options to gain SSH access.
8. Once you have successfully SSH'd into the machine, run the following command to expand the filesystem: `sudo xfs_growfs /export/home-01/`

(troubleshooting:reset-github-app)=
## Resetting a GitHub OAuth app when users are faced with a `403 Forbidden` error at login

```{warning}
These steps require you to have **admin** privileges on the GitHub org the hub is trying to authenticate against.
If you don't have these privileges, ask the Community Representative to grant them to you.
You can remove yourself from the org after establishing that the problem has been rectified.
```

When we setup authentication to use [GitHub orgs or teams](auth:github-orgs), we create an OAuth app in the 2i2c org, regardless of which org we are authenticating with.
Upon the first login, the admins of the _target_ org need to grant permissions to this app to read their org info.
If they don't do this correctly, all users will report a `403 Forbidden` error when they try to login.

```{note}
If this community has a staging and prod hub, you will need to repeat this process on both hubs
```

1. Find and select the appropriate [OAuth app in the 2i2c GitHub org](https://github.com/organizations/2i2c-org/settings/applications)
2. Under "General" settings for the app, click the "Revoke all user tokens" button.
   For all users that have previously attempt to login, this will force them to login again. Including you!
3. Log into the affected hub again. You will repeat the OAuth flow and be asked to authorise the OAuth app again.
   You will be presented with a list of all the GitHub orgs related to your account.
   Some will already be authorised and have a green tick next to them, others where you are a member will have a "Request" button next to them.
   Orgs where you are an admin will have a "Grant" button next to them. Click the "Grant" button next to the _target_ org before clicking the green "Authorize" button.
   For example, see the below screenshot where we wish to grant the `nasa-cryo-staging` OAuth app access to the `binderhub-test-org` org.

   ```{figure} ../images/granting-org-access-to-oauth-app.jpg
   How to grant org access to an OAuth app on GitHub
   ```

The OAuth app will now have the correct permissions to read the org info and hence users should be able to successfully log into their hub.
