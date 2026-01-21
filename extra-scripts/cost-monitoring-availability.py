"""
Script to update data used in `docs/topic/monitoring-alerting/cost-monitoring-availability.md`
"""

import pandas as pd
from ruamel.yaml import YAML

from docs.helper_programs.hub_info_table import get_cluster_grafana_url
from docs.helper_programs.utils import get_cluster_provider, get_clusters_list

yaml = YAML(typ="safe", pure=True)

clusters_yaml = get_clusters_list()

avail_list = []

for c in clusters_yaml:
    cluster_config = yaml.load(c)
    cluster_name = cluster_config["name"]
    provider = get_cluster_provider(cluster_config)
    grafana_url = get_cluster_grafana_url(cluster_config, c.parent)
    if provider != "aws":
        cost_monitoring_enabled = False
        cost_tags_active = False
    else:
        cost_monitoring_enabled = True
        if cluster_config["aws"]["billing"]["paid_by_us"] is True:
            cost_tags_active = True
    avail_list.append(
        {
            "name": cluster_name,
            "grafana_url": grafana_url,
            "provider": provider,
            "cost_monitoring_enabled": cost_monitoring_enabled,
            "cost_tags_active": cost_tags_active,
        }
    )

df = pd.json_normalize(avail_list)
df.to_csv("data.csv", index=False)
