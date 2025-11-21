# Internal Tooling cluster

To run 2i2c as an organization smoothly, we have to run *some* small pieces of
infrastructure that aren't directly related to any specific community. We maintain
an internal tooling cluster on GCP for these.

## What should *never* go on the internal tooling cluster

2i2c's [right to replicate](https://2i2c.org/right-to-replicate/) constrains our
technical design choices, and specifically constraints how we can use our internal
tooling cluster. We must **never** have a community's hubs depend on the internal
tooling cluster for any functionality, as it means that they will not be able to
leave 2i2c without losing some functionality. If the internal tooling cluster goes
down, it should not affect any communities, only 2i2c's operations.

A good heuristic is that community hubs should never make outbound calls to anything
hosted on the internal tooling cluster. This also has good security properties, as
it prevents compromise of one community's cluster from affecting other communities.

## What does go on the internal tooling cluster

In general, for 2i2c's operations, we should attempt to *buy* tooling than *build* it
as long as it's not part of the core service we offer. Internal tooling is by definition
not a core part of the services we offer, so we should attempt to outsource that as much
as possible.

So we should deploy things to the internal tooling cluster as a last resort, after having
exhausted other options.

## What *is* deployed on the internal tooling cluster

Currently, the following are deployed on the internal tooling cluster

### Prometheus with long term metrics storage

We run a *small* prometheus instance that uses [federation](https://prometheus.io/docs/prometheus/latest/federation/)
to mirror *specific* metrics from all our communities' prometheus servers. This is
important for our operational capabilities since prometheus data goes away when we
decommission a community's infrastructure.

We only pick up an allow listed set of metrics from each prometheus, with an allowlist
of labels as well to prevent potential PII leaking and reduce [cardinality explosions](https://grafana.com/blog/2022/02/15/what-are-cardinality-spikes-and-why-do-they-matter/).
