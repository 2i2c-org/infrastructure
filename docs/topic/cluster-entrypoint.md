(topic:cluster-entrypoint)=
# Cluster Entrypoint (for HTTP & HTTPS Traffic)

We have a custom `Service` of type `LoadBalancer` called
`cluster-entrypoint` that provides a single, stable external
IP for all HTTP and HTTPS traffic ingress into the cluster.
We point it to pods via label selectors based on which ingress
controller we are using at any given moment. This allows us
to have a single, stable external IP independent of how we
handle traffic routing - via an Ingress controller, or in the
future, via a GatewayAPI controller. Simply routing traffic to
different pods based on selectors allows us to have a low overhead,
zero downtime way to switch ingress controllers (or to a gateway
controller) in the future, without having to put our users through
downtime as we wait for DNS to propagate.

We have [additional documentation](howto:migrate-ingress) on
migrating between ingress controllers.