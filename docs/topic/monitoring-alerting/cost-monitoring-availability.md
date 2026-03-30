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

```{note}
Update `docs/csv/cost-monitoring.csv` used to generate this table by running `extra-scripts/cost-monitoring-availability.py` in your local dev environment.
```

```{csv-table}
:header-rows: 1
:file: ../../csv/cost-monitoring.csv
```

% DataTables config to make the table above look nice
<link rel="stylesheet"
      href="https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css">
<script type="text/javascript"
        src="https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready( function () {
    $('.table').DataTable( {
        "order": [[ 0, "asc" ]],
        "pageLength": 25,
    });
} );
</script>
<style>
    table {
        font-size: .7em;
    }

    table th, table td {
        padding: 0;
    }
</style>
