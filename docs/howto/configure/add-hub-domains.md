# Add additional domains to a hub

Existing pilot-hubs in the two 2i2c-managed clusters, have a subdomain created and assingned to them on creation,
that respects the following naming convention, based on which domain name and cluster they are part of:

- `<name-of-the-hub>.pilot.2i2c.cloud` - for the ones in the 2i2c cluster and *pilot.2i2c.cloud* domain
- `<name-of-the-hub>.cloudbank.2i2c.cloud` - for the ones in the cloudbank cluster and *cloudbank.2i2c.cloud* domain

But other domains can be easily linked to the same hub in a cluster if needed.

Assuming there is a hub named `foo` in the `2i2c` cluster and we want to add the `foo.edu` domain to it, one would:

1. **Point the `foo.edu` domain to the right cluster.**

    Create a [CNAME](https://en.wikipedia.org/wiki/CNAME_record) entry from the new domain, `foo.edu`, that points to the
    existing `foo.pilot.2i2c.cloud`, where the `foo` hub already runs.

    This will map the new domain name, `foo.edu`, to the default one `foo.pilot.2i2c.cloud` - *the canonical name* and will
    make sure `foo.edu` points to the right cluster, no matter which IP address the cluster has.

2. **Point the `foo.edu` domain to the right hub.**

    Since all the hubs in a cluster are running at the same IP address, but are available at different subdomains,
    we also need a way to specify which hub in this cluster we want the new domain and subsequent requests to point to.

    For this to happen we need to add the new domain to the config for the hub under
    `config/hubs`, under the `domain` key.

      ```yaml
      - name: foo
        cluster: 2i2c
        domain:
          - foo.pilot.2i2c.cloud # default domain
          - foo.edu # additionl domain
        (...)
      ```
