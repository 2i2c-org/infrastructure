(auth:google)=
# Google Hosted Domains


## How-to setup Google OAuth client

1. **Create a Google OAuth App.**
   This can be achieved by following [Google's documentation](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred).
   - Navigate to [APIs and Services](https://console.cloud.google.com/apis/credentials).
   - Press the button 'Create Credentials' and select 'OAuth client ID'
   - Then there are a series of questions to complete:
     - Application Type: Web Application
     - Name: [cluster]-[hub] (e.g. cloudbank-sou)
     - Authorized redirect URIs: https://[hub].[cluster].2i2c.cloud/hub/oauth_callback (e.g. https://sou.cloudbank.2i2c.cloud/hub/oauth_callback)
   - Copy or download the Client ID and Client secret from the pop-up
   - Once you have created the OAuth app, then use the Client ID and secret in the step below 

2. **Create or update the appropriate secret config file under `config/clusters/<cluster_name>/<hub_name>.secret.values.yaml`.**
   You should add the following config to this file, pasting in the client ID and secret you generated in step 1.

    ```yaml
    jupyterhub:
      hub:
        config:
          GoogleOAuthenticator:
            client_id: CLIENT_ID
            client_secret: CLIENT_SECRET
    ```

    ````{note}
    Add the `basehub` key above the `jupyterhub` key for `daskhub` deployments.
    For example:

    ```yaml
    basehub:
      jupyterhub:
        ...
    ```
    ````

    ```{note}
    Make sure this is encrypted with `sops` before committing it to the repository!

    `sops --output config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml --encrypt config/clusters/<cluster_name>/<hub_name>.secret.values.yaml`
    ```

3. **If not already present, add the secret hub config file to the list of helm chart values files in `config/clusters/<cluster_name>/cluster.yaml`.**
   If you created the `enc-<hub_name>.secret.values.yaml` file in step 2, add it to the `cluster.yaml` file like so:

   ```yaml
   ...
   hubs:
     - name: <hub_name>
       ...
       helm_chart_values_files:
         - <hub_name>.values.yaml
         - enc-<hub_name>.secret.values.yaml
     ...
   ```

4. **Edit the non-secret config under `config/clusters/<cluster_name>/<hub_name>.values.yaml`,**

    ```yaml
    jupyterhub:
      hub:
        config:
          JupyterHub:
            authenticator_class: google
          GoogleOAuthenticator:
            username_claim: email
            hosted_domain:
            - [domain] (e.g. go.pasadena.edu)
            strip_domain: false
            allow_all: true
          Authenticator:
            admin_users:
            - ...
            - ...
    ```

5. Run the deployer as normal to apply the config.

