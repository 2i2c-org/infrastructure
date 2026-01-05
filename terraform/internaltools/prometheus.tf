data "sops_file" "encrypted_prometheus_configs" {
  for_each    = { for f in local.encrypted_prometheus_files : f.cluster => f }
  source_file = each.value.encrypted_file
}

# We create the disk for the federated prometheus instance separately, so we
# can have reliable backups and it doesn't get lost due to any issues with
# the cluster.
resource "google_compute_disk" "prometheus_disk" {
  name    = "federated-prometheus-disk"
  type    = "pd-balanced"
  zone    = "us-central1-b"
  size    = var.prometheus_disk_size
  project = var.project_id

  lifecycle {
    prevent_destroy = true
  }
}

resource "kubernetes_namespace" "prometheus_namespace" {
  metadata {
    name = var.prometheus_namespace
  }
}

resource "kubernetes_persistent_volume" "prometheus_disk" {
  metadata {
    name = "federated-prometheus-disk"
  }

  spec {
    capacity = {
      storage = format("%sGi", var.prometheus_disk_size)
    }

    access_modes = ["ReadWriteOnce"]

    persistent_volume_source {
      csi {
        driver        = "pd.csi.storage.gke.io"
        volume_handle = google_compute_disk.prometheus_disk.id
        # Explicitly needs to be set so it's formatted and permissions are set right
        fs_type = "ext4"
      }

    }
  }
}

# Can't use the resource directly because of https://github.com/hashicorp/terraform-provider-kubernetes/issues/872
resource "kubernetes_manifest" "prometheus_disk" {
  depends_on = [kubernetes_namespace.prometheus_namespace]
  manifest = {
    apiVersion = "v1"
    kind       = "PersistentVolumeClaim"
    metadata = {
      name      = "federated-prometheus-disk"
      namespace = var.prometheus_namespace
    }
    spec = {
      resources = {
        requests = {
          storage = format("%sGi", var.prometheus_disk_size)
        }
      }
      accessModes      = ["ReadWriteOnce"]
      storageClassName = ""
      volumeName       = kubernetes_persistent_volume.prometheus_disk.metadata[0].name
    }

  }

}

data "sops_file" "encrypted_prometheus_creds" {
  source_file = "secret/enc-prometheus-creds.secret.yaml"
}


resource "helm_release" "prometheus" {
  depends_on = [kubernetes_namespace.prometheus_namespace]
  name       = "prometheus"
  namespace  = var.prometheus_namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  version    = "28.0.0"

  values = [
    file("${path.module}/prometheus.yaml"),
    yamlencode(local.prometheus_config)
  ]
}

locals {
  cluster_yamls = [for f in fileset(path.module, "../../config/clusters/*/cluster.yaml") : yamldecode(file(f))]
  # A list of all prometheus servers
  prometheuses = flatten([
    for cy in local.cluster_yamls : [
      for f in cy["support"]["helm_chart_values_files"] : {
        # Requires the directory of the cluster file matches the cluster name
        "domain" : yamldecode(file("../../config/clusters/${cy.name}/${f}"))["prometheus"]["server"]["ingress"]["hosts"][0],
        "cluster" : cy["name"]
      } if !startswith(f, "enc-")
    ]
  ])
  prometheus_domain_maps = { for p in local.prometheuses : p.cluster => p.domain }
  encrypted_prometheus_files = flatten([
    for cy in local.cluster_yamls : [
      for f in cy["support"]["helm_chart_values_files"] : {
        # Requires the directory of the cluster file matches the cluster name
        "cluster" : cy["name"]
        "encrypted_file" : "../../config/clusters/${cy.name}/${f}"
        "domain" : local.prometheus_domain_maps[cy["name"]]
      } if startswith(f, "enc-")
    ]
  ])


  scrape_configs = flatten([
    for p in local.encrypted_prometheus_files : [
      for m in var.federated_metrics_allowlist : [
        {
          job_name     = "federate-${p.cluster}-${m.name}"
          metrics_path = "/federate"

          params = {
            "match[]" : [
              "{__name__=~'${m.metric_regex}'}"
            ]
          }

          # We explicitly only keep the labels we want and nothing else.
          # Remember to use metric_relabel_configs (happens after scrape)
          # rather than relabel_configs (before scrape). See https://www.robustperception.io/relabel_configs-vs-metric_relabel_configs/
          # Reference docs: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#relabel_config
          metric_relabel_configs = [
            {
              # Add a 'cluster' label to all metrics so we know where they are from
              source_labels = ["__name__"]
              action        = "replace"
              target_label  = "cluster"
              replacement   = p.cluster
            },
            {
              action = "labelkeep"
              # prometheus uses internal labels as well here when it's matching against labelkeep
              # so we must explicitly specify them, or they'll also be dropped and prometheus will
              # complain. We also mention cluster here, as that's a label we add explicitly.
              regex = "__name__|__address__|__scrape_interval__|__scrape_timeout__|__scheme__|__metrics_path__|cluster|${m.labels_regex}"
            }
          ]

          static_configs = [
            {
              targets = [
                "${p.domain}:443"
              ]
            }
          ]

          scheme = "https"
          basic_auth = {
            username : sensitive(data.sops_file.encrypted_prometheus_configs[p.cluster].data["prometheusIngressAuthSecret.username"]),
            password : sensitive(data.sops_file.encrypted_prometheus_configs[p.cluster].data["prometheusIngressAuthSecret.password"])
          }
        }
      ]
    ]
  ])

  prometheus_config = sensitive({
    server : {
      ingress : {
        enabled : true,
        ingressClassName : "nginx",
        annotations : {
          "cert-manager.io/cluster-issuer" : "letsencrypt-prod"
        },
        hosts : ["federated-prometheus.internaltools.2i2c.org"],
        tls : [{
          secretName : "prometheus-tls",
          hosts : ["federated-prometheus.internaltools.2i2c.org"]
        }]
      }
      # See https://github.com/prometheus-community/helm-charts/issues/1255 for
      # how and why this is configured this way
      extraArgs : {
        "web.config.file" : "/etc/config/web.yml"
      },
      probeHeaders : [
        {
          name : "Authorization",
          value : sensitive(format("Basic %s", base64encode(format("%s:%s",
            data.sops_file.encrypted_prometheus_creds.data["prometheusCreds.username"],
            data.sops_file.encrypted_prometheus_creds.data["prometheusCreds.password"]
          ))))
        }
      ]
    },
    serverFiles : {
      "prometheus.yml" : {
        scrape_configs : local.scrape_configs
      },
      "web.yml" : {
        # See https://github.com/prometheus-community/helm-charts/issues/1255 for
        # how and why this is configured this way
        basic_auth_users : {
          sensitive((data.sops_file.encrypted_prometheus_creds.data["prometheusCreds.username"])) : sensitive(bcrypt(data.sops_file.encrypted_prometheus_creds.data["prometheusCreds.password"]))
        }
      }
    }
  })
}
