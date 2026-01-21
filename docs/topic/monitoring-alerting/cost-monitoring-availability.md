# Cost Monitoring Availability

The [Cost Monitoring System](./cost-monitoring-system.md) is available on select clusters. Its availability depends on the following factors:

- cost monitoring is currently available only on clusters deployed on AWS
- activating cost allocation tags using appropriate AWS account IAM permissions either through
  - 2i2c-managed SSO, where cloud costs are passed through to communities
  - Standalone accounts, where cloud costs are directly charged to communities
  - Another third party provider, such as [Cloudbank](https://www.cloudbank.org/).
