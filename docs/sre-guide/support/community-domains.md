# Provide the hub on a community maintained domain

Some communities want the hub to be available under a domain they control,
rather than as `<something>.2i2c.cloud`. This runbook describes how to handle
requests for such custom domains.

## Terminology

- **2i2c managed domain**

  A subdomain under `.2i2c.cloud` that 2i2c engineers have full control over.
  This will *always* be an `A` (GCP, Azure) or `CNAME` (AWS) record pointing to the
  external IP of the `nginx-ingress` service in the cluster.

  ```{note}

  You can verify this by running `kubectl -n support get svc
  support-ingress-nginx-controller` and looking under the `EXTERNAL IP` column.
  ```

- **community managed domain**

  Any domain not under 2i2c control that the community wants the
  hub to be available at. The community will manage domain registration and DNS
  records for this domain. This will *always* be a `CNAME` pointing to a 2i2c
  managed domain.


```{important}
The reason we ask a community to set CNAMEs that point to the record in our
domain is so that we only need to update _our_ DNS records if the external IP
address of our load balancing service changes. No changes will be required
upstream in the community managed DNS system.
```

## Providing the community instructions for changes they need to make

The community will have to set up appropriate DNS records first before we can
make progress, but we will have to tell them what records to set up.

In addition, if Auth0 is being used as the authentication provider, the
community will also need to make specific changes to the Auth0 application they
gave us.

The following template may be used to communicate this to the community.

```markdown

Hi {{ name }},
​
The actions we need from you are:

{{ for each hub }}
- Make a CNAME DNS record, from {{ community managed domain }} pointing to {{ 2i2c managed domain }}
{{ end for }}

{{ if auth0 is in use}}
-. Since you manage the auth0 setup, you'll need to make the following changes to the Auth0 application:
    {{ for each hub }}
    a. Add https://{{ community managed domain}}/hub/oauth_callback to the list of allowed callback URLs.
    b. Add https://{{ community managed domain}} to the list of allowed logout redirect URLs
    {{ end }}
{{ end if }}

Let us know when these are done and we'll do the config changes required on our part!

```

Since a wide variety of domain registrars / DNS record management software may
be used, we can not provide support for actually making these changes - that is
a community responsibility.

## Verify the DNS changes

Once the community has made the changes, we can test that with the following command:

```bash
dig +short -t cname {{ community managed domain }}
```

Should provide the output of the 2i2c managed domain we have set up for the hub. If
it does not, wait for about 15 minutes and try again - DNS propagation may take a while.

## Preparing the configuration change

1. In the `<hub-name>.values.yaml` file, change `jupyterhub.ingress.hosts` and
   `jupyterhub.ingress.tls`, replacing the 2i2c domain name with the community
   provided domain name.

2. In `cluster.yaml` file for the cluster the hubs are
   in, change the `domain` field to point to the community managed domain.

3. If Auth0 is being used, change `jupyterhub.hub.config.CustomAuth0OAuthenticator.logout_redirect_to_url`
   to point to the community managed domain.

4. If GitHub Authentication is being used, change the domain used in the URL in
   `jupyterhub.hub.config.GitHubOAuthenticator.oauth_callback_url` to point to the community
   managed domain.

5. If CILogon Authentication is being used, change the domain used in the URL in
   `jupyterhub.hub.config.CILogonOAuthenticator.oauth_callback_url` to point to the community
   managed domain.

6. In the `support.values.yaml` file for the cluster in which the hubs are, we set up redirects
   so folks who go to the older domains will get redirected to the new domain.

   ```yaml
   redirects:
     rules:
       - from: <2i2c-managed-domain>
         to: <community-managed-domain>
   ```

7. Make a PR with your changes.

## Deploying the configuration change

If there is a staging hub in the list of hubs being changed, you can [deploy manually](hubs:manual-deploy)
to test these changes. To test the redirects manually, you can use the [deploy-support](deploy-support-chart:manual)
command.

### Determine a possible deployment time window

If this is a currently running hub with active users, this change will be *disruptive*, as the old
URLs will no longer work. Communicate this to the community, and find a useful time to deploy
the change that will be the least disruptive.

However, most often this is done *before* there is any real usage on the hub, and timing this
is not a consideration.

### Authentication updates

**Just** before deployment, we should change the Authorized Callback URLs in the appropriate
upstream authentication provider we use. We delay this to just before the deployment, since in
most providers we can have only *one* authorized callback URL. As soon as we change this URL to
point to the new domain, users can not log in to the old domain anymore!

#### GitHub Authentication

1. Open the appropriate GitHub App from the [list of OAuth apps](https://github.com/organizations/2i2c-org/settings/applications)
   in the 2i2c-org GitHub org.
2. Change the **Homepage URL** to point to the new community managed domain.
3. Change the **Authorization callback URL** to point to the new community managed domain. This
   should match the value in `jupyterhub.hub.config.GitHubOAuthenticator.oauth_callback_url`.
4. Hit the **Update application** button.

#### CILogon Authentication

Use the `deployer cilogon-client` command to update the existing CILogon client application.

This commands needs to be passed the cluster name, the hub name and the **new community managed domain**.

```bash
deployer cilogon-client update {{ cluster name }} {{ hub name }} {{ community managed domain}}
```

You can verify this was updated correctly by looking at the output of the following command:

```bash
deployer cilogon-client get {{ cluster name }} {{ hub name }}
```

The `redirect_uris` field should have the new community managed domain, and should match
the value in `jupyterhub.hub.config.CILogonOAuthenticator.oauth_callback_url``

#### Auth0 Authentication

Since Auth0 supports multiple active authorized callback URLs, and we asked the community to
*add* (not replace) authorized callback URLs, no action is necessary here.

### Deploy the change

Merge the pull request you made!

### Test the change

After the deployment has completed, and re-test to make sure that the following features work:

a. Logging in to the hub
b. Spawning a server
c. Logging out of the hub

### Let the community know

Once you've verified that the new domain works ok, communicate to the community that this change
is complete.
