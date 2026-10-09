# Cost Monitoring Availability

The [Cost Monitoring System](./cost-monitoring-system.md) is available on select clusters. Its availability depends on the following factors:

- cost monitoring is currently available only on clusters deployed on AWS
- active cost allocation tags using appropriate AWS account IAM permissions either through
  - 2i2c-managed SSO, where cloud costs are passed through to communities
    - we manage this, so we can activate tags on behalf of communities
  - Standalone accounts, where cloud costs are directly charged to communities
    - this requires a technical contact with IAM permissions to activate on our behalf
  - Another third party provider, such as [Cloudbank](https://www.cloudbank.org/)
    - we have no IAM permissions here, so we require a technical contact to activate cost tags on our behalf.

## Reference table

A list of clusters with cost monitoring enabled[^1].

[^1]: This is here via `{include}` and the source is at: `docs/csv/cost-monitoring.txt`.
    The `.txt` file is auto-generated if you build the docs with `nox -s docs`.

:::{tabulator}
:pagination:
:page-size: 25
:search:
:::

```{include} ../../csv/cost-monitoring.txt
```
