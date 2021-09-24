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
