## FIXME: Describe this Helm chart

Describe more about this Helm chart. What are the assumptions made within it for
example, and what are the assumptions on basehub and daskhub with regards to
what is available within the k8s cluster. Do they rely on ingress-nginx and
cert-manager for example?

### Observations
- This Helm chart contains config specific to 2i2c k8s cluster, as noted by a
  domain name configured for grafana.
- This Helm chart contain a template creating a GCP specific k8s StorageClass
