
# Migrate from one ingress controller to another

## Why migrate ingress controllers?

In 2026, the policy of best-effort maintenance of the Ingress NGINX Controller ended. Following the announcement of this plan, a considerable amount of discussion has taken place amongst Kubernetes users around the topic of a replacement.

In the near term, 2i2c has decided to migrate to the [official NGINX Ingress Controller](https://docs.nginx.com/nginx-ingress-controller/install/helm/open-source/). This is likely not a "permanent" solution — alongside the Ingress NGINX Controller deprecation, the Kubernetes Ingress API _itself_ is also frozen, with the Kubernetes project recommending the Gateway API instead. Although there has not been an announcement that the Ingress API will become deprecated in future, we may need/want to migrate to the Gateway API down the road.

```{note} Concerns with ingress migration

Naively using the provided LoadBalancer (LB) from each ingress controller requires the update of DNS records to migrate domains from one LB to another. During this time, the cluster infrastructure will be unavailable to some of external users.

When migrating between controllers, we also want to avoid re-issuing TLS certificates, which are a "costly" resource.
```

## How to migrate from Ingress NGINX Controller

To facilitate zero downtime migration between controllers, we have introduced a new LoadBalancer ingress service. The purpose of this service is to provide a static external IP address that lives independently of the ingress controller. Consequently, we no longer need ingress controllers to create their own LBs — we can use simple clusterIP services.

For clusters that are still running Ingress NGINX Controller, the existing DNS records point to the controller-managed LoadBalancer service external IP. To migrate between two ingress controllers `ingress-nginx` and `nginx-ingress`, we must perform two separate migrations:

(migrate-ingress:migrate-dns)=
### Migrate DNS records to dedicated LoadBalancer service

We recently updated the support chart to enable the LoadBalancer service on all hubs. In this phase, we must migrate the DNS records for the cluster to the `traffic-entrypoint` LoadBalancer external IP. We can easily lookup the LB hostname with:

```bash
kubectl --namespace=support get service/traffic-entrypoint  --template="{{(index .status.loadBalancer.ingress 0).hostname}}"
```

We must migrate the DNS records for the domain to point to this external IP. During the migration, both the "new" LB and existing ingress-nginx owned LB must be available.


(migrate-ingress:switch-controller)=
### Switch to official `nginx-ingress` controller

Once the DNS records have been updated to point to the `traffic-entrypoint` LB, we can safely transition to the official `ingress-nginx` service:

1. Enable the `nginx-ingress` service in the support chart with
   ```{code-block} yaml
   nginx-ingress:
     # Enable controller
     enabled: true
     controller:
       ingressClass:
         # Claim the `nginx` ingress class
         create: true
   ```
1. Disable the `ingress-nginx` controller:
   ```{code-block} yaml
   ingress-nginx:
     controller:
       # Turn off controller
       replicaCount: 0
       # Let go of the `nginx` ingress class
       ingressClassResource:
         enabled: false
   ```
1. Point the `traffic-entrypoint` LB to the new `nginx-ingress` service:
   ```{code-block} yaml
   trafficEntrypoint:
     targetController: nginx-ingress
   ```

## How to handle future migrations 
Once all clusters are using the `traffic-entrypoint` LB for their DNS records, it should be trivial to migrate to a new ingress controller or Gateway that establishes a clusterIP service. Once a new controller/gateway is introduced, simply point the `traffic-entrypoint` LB at the new service pods.

