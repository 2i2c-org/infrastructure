# Add a new hub in a AWS kops-based cluster

The idea behind this guide is showcase the process of setting up a 
[kops](https://kops.sigs.k8s.io/getting_started/aws/)-based AWS
cluster and manually deploy a new hub on top of it using our deployer tool.
This is a preliminary but fully functional and manual process. Once
[#381](https://github.com/2i2c-org/pilot-hubs/issues/381) is resolved, we should be able
to automate the hub deployment process as we currently do with the GKE-based hubs.

```{note}
We will continue working toward a definitive one once we figured out some of the
discussions outlined in [#431](https://github.com/2i2c-org/pilot-hubs/issues/431).
```

## Create an AWS kops-based cluster

Follow the instructions in [](new-cluster:aws).

## Deploy the new hub

1. First, `cd` back to the root of the repository

2. Generate a kubeconfig that will be used by the deployer.
   To do so, run the following command: 

   ```bash
   KUBECONFIG=secrets/<cluster_name>.yaml kops export kubecfg --admin=730h    <cluster_name>hub.k8s.local
   ```

3. Encrypt (in-place) the generated kubeconfig with sops.

   ```bash
   sops -i -e secrets/<cluster_name>.yaml
   ```

4. Generate a new config file for your cluster.

   You can use of the existing cluster config files as a "template" for your cluster (for example, [here is the Farallon Institute config file](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs/farallon.cluster.yaml)).
   You may need to tweak names, `serverIP` and singleuser's images references.
   Make sure you set up the `profileList` section to be compatible with your kops cluster (ie. match the `node_selector` with the proper `instance-type`).

5. Set `proxy.https.enabled` to `false`.
   This creates the hubs without trying to give them HTTPS, so we can appropriately create DNS entries for them.

6. Deploy the hub (or hubs in case you are deploying more than one) without running the test with

   ```bash
   python3 deployer deploy <cluster_name> --skip-hub-health-test
   ```

7. Get the AWS external IP for your hub with (supposing your hub is `staging`):

   ```bash
   kubectl -n staging get svc proxy-public
   ```

   Create a CNAME record for `staging.foo.2i2c.cloud` and point it to the AWS external IP.

   ```{note}
   Wait for about 10 minutes to make sure the DNS records actually resolves properly.
   If you are deploying `prod` hub as well, you will need to repeat this step for `prod`.
   ```

8. Set `proxy.https.enabled` to `true` in the cluster config file so we can get HTTPS.

9. Finally run the deployer again with 

   ```bash
   python3 deployer deploy <cluster_name>
   ```

This last run should setup HTTPS and finally run a test suite.
