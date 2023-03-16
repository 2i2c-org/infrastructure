(grafana-dashboards:github-auth)=
# Enable GitHub authentication for Grafana

We can enable GitHub authentication against a Grafana instance in order to allow access to the dashboards for hub administrators as well as 2i2c engineers.

To enable logging into Grafana using GitHub, follow these steps:

1. Create a GitHub OAuth application following [Grafana's documentation](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/github/#configure-github-oauth-application).
   - Create [a new app](https://github.com/organizations/2i2c-org/settings/applications/new) inside the `2i2c-org`.
   - When naming the application, please follow the convention `<cluster_name>-grafana` for consistency, e.g. `2i2c-grafana` is the OAuth app for the Grafana running in the 2i2c cluster
   - The Homepage URL should match that in the `grafana.ingress.hosts` field of the appropriate cluster `support.values.yaml` file in the `infrastructure` repo. For example, `https://grafana.pilot.2i2c.cloud`
   - The authorisation callback URL is the homepage url appended with `/login/github`. For example, `https://grafana.pilot.2i2c.cloud/login/github`.
   - Once you have created the OAuth app, create a new client ID, generate a client secret and then hold on to these values for a future step

2. Edit using `sops` the encrypted `enc-support.secret.values.yaml` file in the chosen cluster directory and add the credentials created in step one:

   ```yaml
   grafana:
     grafana.ini:
       auth.github:
         client_id: <client-id>
         client_secret: <client-secret>
   ```

3. Edit the `support.values.yaml` file in your chosen cluster directory and add the Grafana GitHub auth config, allowing the specific GitHub organization you wish to allow login.

   ```yaml
   grafana:
     grafana.ini:
       server:
         root_url: https://<grafana.ingress.hosts[0]>
       auth.github:
         enabled: true
         # allowed_organizations should be a space separated list
         allowed_organizations: 2i2c-org
   ```

   ```{note}
   Checkout the [Grafana documentation](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/github) for more info about authorizing users using other types of membership than GitHub organizations.
   ```
