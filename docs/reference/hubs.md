# JupyterHubs we manage

Most of our JupyterHubs are centrally configured and deployed in [the `pilot-hubs/` repository](https://github.com/2i2c-org/pilot-hubs).
However, there are a few hubs that are special-cased as well, and we list both on this page.

## A complete list of our JupyterHubs

Here's a list of running hubs.

<div class="full-width">

```{csv-table}
:header-rows: 1
:file: ../tmp/hub-table.csv
```

</div>



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

## Special-cased hubs

There are some hubs that we treat differently from others.
This is heavily discouraged, but may be necessary to meet the needs of certain communities before our deployment infrastructure can accommodate them.

### University of Toronto

We run a JupyterHub for the University of Toronto.
This is configured and deployed at [the `utoronto-deploy` repository](https://github.com/utoronto-2i2c/jupyterhub-deploy).

**Special cases**

There are a few special cases about this deployment:

- **Authentication**: Uses [Azure Active Directory](https://azure.microsoft.com/en-us/services/active-directory/).
  
  This assigns each username a unique ID, like `adb7ebad-9fb8-481a-be4c-6c0a8b4se670`.
- **U. Toronto provides us credentials for authentication**: Our hub uses a credential that allows us to authenticate with the U of T AzureAD service.
  This credential must be **renewed annually** by the University of Toronto.
  They must send us the new credential each year, or the hub will no longer be able to authenticate users.
  See [this incident issue](https://github.com/2i2c-org/pilot-hubs/issues/637) for an example of what happens if these credentials aren't renewed.
- **User image must be manually built and pushed**: The [user image for this hub](https://github.com/utoronto-2i2c/jupyterhub-deploy/tree/staging/deployments/utoronto/image) is quite large, as it accommodates a number of different use-cases. GitHub actions may not be able to build it, and so we need to build and pushed to the image registry.
- **Runs on U Toronto Azure project**. This hub runs on the U of T Azure project, and their administrators must provide us access to their cloud in order to directly work on the hub.
  Currently, only @yuvipanda and @GeorgianaElena have access to this hub.
