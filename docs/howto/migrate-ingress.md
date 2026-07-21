(howto:migrate-ingress)=
# Migrate from one ingress controller to another or to Gateway API

## Why migrate ingress controllers?

In 2026, the policy of best-effort maintenance of the Ingress NGINX Controller ended. Following the announcement of this plan, a considerable amount of discussion has taken place amongst Kubernetes users around the topic of a replacement.

In the near term, 2i2c has decided to migrate to the [official NGINX Ingress Controller](https://docs.nginx.com/nginx-ingress-controller/install/helm/open-source/). This is likely not a "permanent" solution — alongside the Ingress NGINX Controller deprecation, the Kubernetes Ingress API _itself_ is also frozen, with the Kubernetes project recommending the Gateway API instead. Although there has not been an announcement that the Ingress API will become deprecated in future, we may need/want to migrate to the Gateway API down the road.

```{note} Concerns with ingress migration

Naively using the provided LoadBalancer (LB) from each ingress controller requires the update of DNS records to migrate domains from one LB to another. During this time, the cluster infrastructure will be unavailable to some of external users.

When migrating between controllers, we also want to avoid re-issuing TLS certificates, which are a "costly" resource.
```

## How to migrate from an existing Controller to another

To facilitate zero downtime migration between controllers, we have introduced a new [LoadBalancer ingress service](https://github.com/2i2c-org/infrastructure/blob/main/helm-charts/support/templates/traffic-entrypoint.yaml). The purpose of this service is to provide a static external IP address that lives independently of the ingress controller. Consequently, we no longer need ingress controllers to create their own LBs — we can use simple clusterIP services.

(migrate-ingress:switch-controller)=
### Switch to another nginx controller

Since the DNS records are pointing to the dedicated `cluster-entrypoint` LB service, we can safely transition to the new `ingress` service:

1. Enable the new ingress (in this case `nginx-ingress`) service in the support chart with
   ```{code-block} yaml
   nginx-ingress:
     # Enable controller
     enabled: true
     controller:
       ingressClass:
         # Claim the `nginx` ingress class
         create: true
   ```
1. Disable original controller (in this case `ingress-nginx`):
   ```{code-block} yaml
   ingress-nginx:
     controller:
       # Turn off controller
       replicaCount: 0
       # Let go of the `nginx` ingress class
       ingressClassResource:
         enabled: false
   ```
1. Point the `cluster-entrypoint` LB to the new ingress service (in this case `nginx-ingress` ):
   ```{code-block} yaml
   clusterEntrypoint:
     targetController: nginx-ingress
   ```

   *Make sure to modify the `cluster-entrypoint` service to conditionally set the correct annotations, depending on which targetController is set.

## Switch to Gateway API

It should be trivial to migrate to a new ingress controller or Gateway that establishes a clusterIP service. Once a new controller/gateway is introduced, simply point the `cluster-entrypoint` LB at the new service pods.
