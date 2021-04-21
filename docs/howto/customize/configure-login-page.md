# Configure the hub login page

Each Hub deployed in a cluster has a collection of metadata about who it is deployed for, and who is responsible for running it. This is used to generate the **log-in page** for each hub and tailor it for the community.

For an example, see [the log-in page of the staging hub](https://staging.pilot.2i2c.cloud/hub/login).

The log-in pages are built with [the base template at this repository](https://github.com/2i2c-org/pilot-homepage). Values are inserted into each template based on each hub configuration.

You may customize the configuration for a hub's homepage at `config.jupyterhub.homepage.templateVars`. Changing these values for a hub will make that hub's landing page update automatically.
Copy the configuration from another hub, and then modify the contents to fit the new hub that is being configured.
