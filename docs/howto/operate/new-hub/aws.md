# Add a hub to an AWS `kops`-based cluster

The idea behind this guide is showcase the process of setting up a
[kops](https://kops.sigs.k8s.io/getting_started/aws/)-based AWS
cluster and manually deploy a new hub on top of it using our deployer tool.
This is a preliminary but fully functional and semi-automatic process. Eventually, we
should be able to fully automate the first hub deployment process as we currently do
with the GKE-based hubs.

```{note}
We will continue working toward a definitive one once we figured out some of the
discussions outlined in [#431](https://github.com/2i2c-org/infrastructure/issues/431).
```

## Create an AWS kops-based cluster (optional)

Follow the instructions in [](new-cluster:aws) if you are not deploying against an
existing cluster.

(new-hub:aws)=
## Deploy the new AWS hub

Follow the steps outlined in [](new-hub:deploy) with the following modifications:

1. Generate a new values file for your hub if there is not an existing one.

   You can use one of the existing hub values files as a "template" for your hub (for
   example, [here is the Farallon Institute staging hub values file](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/farallon/staging.values.yaml)).
   You may need to tweak names, `serverIP` and singleuser's images references.
   Make sure you set up the `profileList` section to be compatible with your kops cluster
   (ie. match the `node_selector` with the proper `instance-type`).

2. Set `proxy.https.enabled` to `false`.
   This creates the hub without trying to give it an HTTPS certificate, so we can appropriately
   create DNS entries for it.

3. Create a Pull Request with the new entries, and get a team member to review it.

4. Once you merge the pull request, the GitHub Actions workflow will detect that a new entry has
   been added to the configuration file.
   It will then deploy a new JupyterHub with the configuration you've specified onto the
   corresponding AWS cluster.

5. Monitor the workflow to make sure that it completes.

6. Get the AWS external IP for your hub with (supposing your hub is `staging`):

   ```bash
   kubectl -n staging get svc proxy-public
   ```

   To perform the above command successfully, you will need to get the kubernetes context.
   If you are working with a EKS cluster, you can get the kubeconfig with (modulo you get
   the credential properly configured):
     ```bash
     aws eks update-kubeconfig --name=<NAME_OF_THE_CLUSTER> --region=<REGION>
     ```
   if you are working with a kops cluster, you can get it with:
     ```bash
     kops export kubecfg --admin --name <NAME_OF_THE_CLUSTER>.k8s.local --state s3://2i2c-<NAME_OF_THE_CLUSTER>-kops-state
     ```

   Create a CNAME record for `staging.foo.2i2c.cloud` and point it to the AWS external IP.

   ```{note}
   Wait for about 10 minutes to make sure the DNS records actually resolves properly.
   If you are deploying `prod` hub as well, you will need to repeat this step for `prod`.
   ```

7. Set `proxy.https.enabled` to `true` in the hub values file so we can get HTTPS.

8. Repeat steps 4 and 5.

```{note}
You need to perform the CNAME record update (step 2 - 6) just once, you will not need to
perform those steps for further deployment on pre-existing hubs.
```
