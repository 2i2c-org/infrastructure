# Set a community-specific domain using a CNAME

We most commonly make hubs available at an address that follows a pattern such
as: `<community-name>.<cluster-name>.2i2c.cloud` or `<community-name>.2i2c.cloud`
(depending on whether the hub is deployed to a shared cluster or a dedicated one
respectively). However, some communities may have their own domain name and may
want their hub to be available at that address instead, for example:
`hub.<community-domain>`. This guide covers the steps required to allow this.

```{attention}
This guide requires that you have completed the steps in the [](deploy-support-chart)
section of the Hub Deployment Guide.
```

## Let the Community Representative know what to do in their DNS provider

In [](deploy-support-chart:dns-records), you probably created a DNS record in
our Namecheap account that looked something like `*.<community-name>` and
pointed it at the external IP address of the NGINX load balancer service that is
deployed as part of the `support` chart. It is unlikely that a 2i2c engineer
will have access to the DNS provider a community are using to manage their
domain name so we must provide them with the steps required for them to proceed.
You can use the template below to comment on the relevant "New Hub - Request
deployment" issue asking them to complete the steps.

```markdown
### Instructions for setting CNAMEs

For the hub to be available at hub.`<community-domain>`, please follow the below steps:

1. Please create a CNAME record in your DNS zone
2. Give the CNAME record an understandable name. This can be anything you want,
   for example, `hub`.
3. Set the following URL as the CNAME target:
   - `<community-name>.2i2c.cloud`  # Or whatever the record in our DNS zone is
4. Let me know when you have done that and I shall redeploy the hub to use the new URL

You can repeat this process to also host the staging hub at staging.hub.`<community-name>`,
but this time, the CNAME record should be called something slightly different,
such as `staging.hub` or whatever you prefer, and the target URL is
`staging.<community-name>.2i2c.cloud`

Hope that makes sense!
```

```{important}
The reason we ask a community to set CNAMEs that point to the record in our
domain is so that we only need to update _our_ DNS records if the external IP
address of our load balancing service changes. No changes will be required
upstream in the community-owned DNS zone.
```

## Update our config to use the new URL

Once the Community Representative has confirmed that they have setup the
required CNAMEs, we must update our config and redeploy the hubs.

At an _absolute minimum_, the `domain` field of the relevant hub entry in the
`cluster.yaml` file needs to be changed to match the new URL.

Additionally, if the method of authentication setup on the hubis associated with
an app, such as [](auth:github-orgs) or [](auth:cilogon), then these extra
changes will also be required:

- Update the OAuth Callback URL stored in our config to match the new URL
- Change the **homepage URL** and the **OAuth Callback URL** defined in the
  settings of the OAuth app to match the new URL

Once you have made these changes and committed them, you can deploy them either
via [CI/CD by merging a PR](cicd) or by [manually running the deployer](hubs:manual-deploy).
