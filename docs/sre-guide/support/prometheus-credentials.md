# User access to Prometheus endpoint

We now enforce HTTP basic authentication at the Prometheus layer.

Hub admins may want direct access to their Prometheus from outside the cluster, e.g. as a datasource for their own [AWS CloudWatch dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_MultiDataSources-Connect.html#MultiDataSources-Prometheus). In this case, we can decide to securely share the credentials with the community.

## Steps

```{tip}
The steps below show how to send the credentials with `age`, but you can also use Bitwarden Send. See [](how-to:send-secrets) for more details.
```

1. Instruct the community to send you a **public** key with [`age`](https://github.com/FiloSottile/age) by running `age-keygen -o key.txt` and link the corresponding [user-facing docs](https://docs.2i2c.org/admin/monitoring/prometheus-api-access/).
2. After they have sent you a public key, place the username and password in a `credentials.txt` file and encrypt it with

  ```bash
  age -r <public-key> -o credentials.txt.age credentials.txt
  ```

3. You can respond and attach the `credentials.txt.age` file with the following message template:

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
