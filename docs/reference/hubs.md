# List of running hubs

Here's a list of running hubs.

<div class="full-width">

```{csv-table}
:header-rows: 1
:file: ../tmp/hub-table.csv
```

</div>

```{note}
About our demo hub

The 2i2c operates a hub for demonstration and experimentation at `demo.pilot.2i2c.org`.
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