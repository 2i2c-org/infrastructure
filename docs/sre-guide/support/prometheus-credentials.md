# User access to Prometheus endpoint

Hub admins may want direct access to their Prometheus from outside the cluster, e.g. as a datasource for their own [AWS CloudWatch dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_MultiDataSources-Connect.html#MultiDataSources-Prometheus).

We can provision an extra set of credentials to the ingress-nginx [basic auth](https://kubernetes.github.io/ingress-nginx/examples/auth/basic/) and securely distribute these to the community

## Steps

1. Update the relevant `enc-support.secret.values.yaml` file under the `config/clusters/<cluster-name>/` folder with another username/password entry

   ```yaml
   prometheusIngressAuthSecret:
     users:
       - username: <output of pwgen -s 64 1>
         password: <output of pwgen -s 64 1>
       - username: <output of pwgen -s 64 1>
         password: <output of pwgen -s 64 1>         
   ```

   ```{tip}
   Make sure you place the extra user credentials **under** the first entry, since the first entry is reserved for internal 2i2c purposes to [register with our central grafana](/hub-deployment-guide/deploy-support/register-central-grafana.md).
   ```

1. Securely send the user credentials to the community

   - Instruct the community to send you a **public** key with [`age`](https://github.com/FiloSottile/age) by running `age-keygen -o key.txt` and link the corresponding [user-facing docs](https://docs.2i2c.org/admin/monitoring/prometheus-api-access/).
   - After they have sent you a public key, place the username and password in a `credentials.txt` file and encrypt it with

      ```bash
      age -r <public-key> -o credentials.txt.age credentials.txt
      ```

   - You can respond and attach the `credentials.txt.age` file with the following message template:

   > Hello {{ name }}
   >
   > We have provisioned credentials for you to access your Prometheus endpoint from https://prometheus.<cluster_name>.2i2c.cloud.
   >
   > Attached is an encrypted file containing the username/password pair. Please run
   >
   > age --decrypt -i key.txt -o credentials.txt credentials.txt.age
   >
   > to retrieve the contents.
   >
   > Personally Identifiable Information (PII) is at risk if the credentials are compromised. Please do not share these credentials through any insecure channels, and notify us immediately if you need to renew them.
   >
   > Thanks!

   ```{warning}
   Personally Identifiable Information (PII) is at risk if the credentials are compromised.
   ```
