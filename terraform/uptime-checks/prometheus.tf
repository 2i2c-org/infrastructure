data "sops_file" "encrypted_prometheus_configs" {
  for_each    = { for f in local.encrypted_prometheus_files : f.cluster => f }
  source_file = each.value.encrypted_file
}

resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  version    = "27.29.0"

  values = [
    file("${path.module}/prometheus.yaml"),
    yamlencode({
      serverFiles : {
        "prometheus.yml" : {
          scrape_configs : local.scrape_configs
        }
      }
    })
  ]
}

locals {
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
              regex  = "__name__|__address__|__scrape_interval__|__scrape_timeout__|__scheme__|__metrics_path__|cluster|${m.labels_regex}"
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
            username : data.sops_file.encrypted_prometheus_configs[p.cluster].data["prometheusIngressAuthSecret.username"],
            password : data.sops_file.encrypted_prometheus_configs[p.cluster].data["prometheusIngressAuthSecret.password"]
          }
        }
      ]
    ]
  ])
}
