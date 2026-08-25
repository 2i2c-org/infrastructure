resource "helm_release" "nginx-ingress" {
  name             = "nginx-ingress"
  namespace        = "ingress"
  create_namespace = true
  repository       = "oci://ghcr.io/nginx/charts"
  chart            = "nginx-ingress"
  version          = "2.4.4"

  values = [
    file("${path.module}/ingress.yaml")
  ]
}

resource "helm_release" "cert-manager" {
  name             = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "1.19.1"

  set = [{
    name  = "installCRDs"
    value = true
  }]
}

resource "kubernetes_manifest" "clusterissuer_letsencrypt_prod" {
  depends_on = [
    helm_release.cert-manager
  ]
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind"       = "ClusterIssuer"
    "metadata" = {
      "name" = "letsencrypt-prod"
    }
    "spec" = {
      "acme" = {
        "email" = "support@2i2c.org"
        "privateKeySecretRef" = {
          "name" = "letsencrypt-prod"
        }
        "server" = "https://acme-v02.api.letsencrypt.org/directory"
        "solvers" = [
          {
            "http01" = {
              "ingress" = {
                "class" = "nginx"
              }
            }
          }
        ]
      }
    }
  }
}


resource "kubernetes_service" "cluster-entrypoint" {
  metadata {
    name      = "cluster-entrypoint"
    namespace = "ingress"
  }
  spec {
    external_traffic_policy = "Local"
    type                    = "LoadBalancer"
    port {
      name        = "http"
      port        = 80
      target_port = 80
    }

    port {
      name        = "https"
      port        = 443
      target_port = 443
    }
    selector = {
      "app.kubernetes.io/instance" = "nginx-ingress"
      "app.kubernetes.io/name"     = "nginx-ingress"
    }
  }
}