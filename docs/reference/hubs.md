# List of running hubs

Here's a list of running hubs.
It is automatically generated from the config stored in the [`config/clusters` folder of the `infrastructure` repository](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters) and can therefore be limited in the information it provides.

```{admonition} Missing information for Azure hubs
Hubs that have `kubeconfig` listed as their provider are most likely running on Azure.
The reason `kubeconfig` is listed as a provider is because that is the mechanism we are using to authenticate to that cluster in the case where we do not have a Service Principal.

Unlike GCP and AWS, Azure does not require the location for authentication and it is therefore not listed in our config files and hence cannot be populated in this table.
```

<div class="full-width">

```{csv-table}
:header-rows: 1
:file: ../tmp/hub-table.csv
```

</div>

```{note}
About our demo hub

The 2i2c operates a hub for demonstration and experimentation at [demo.2i2c.cloud](https://demo.2i2c.cloud).
This hub is primarily for the 2i2c team to try things out, and it may change or break occasionally.
Team members should feel free to experiment with this hub and try out new functionality and features they'd like to show off to others.
```


<!-- DataTables to make the table above look nice -->
<link rel="stylesheet"
      href="https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css">
<script type="text/javascript"
        src="https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js"></script>

<script>
$(document).ready( function () {
    $('table').DataTable( {
        "order": [[ 0, "template" ]],
        "pageLength": 50
    });
} );
</script>
