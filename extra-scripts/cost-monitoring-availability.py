"""
Script to update data used in `docs/topic/monitoring-alerting/cost-monitoring-availability.md`
"""

import json

import pandas as pd
import requests
from ruamel.yaml import YAML
from yarl import URL

from deployer.infra_components.cluster import Cluster
from docs.helper_programs.hub_info_table import get_cluster_grafana_url
from docs.helper_programs.utils import get_cluster_provider, get_clusters_list

yaml = YAML(typ="safe", pure=True)


def check_cost_data(cluster_name: str):
    """
    Query jupyterhub-cost-monitoring-service for cost data.
    """
    cluster = Cluster.from_name(cluster_name)
    grafana_token = cluster.get_grafana_token()
    grafana_url = URL(cluster.get_grafana_url())
    api_url = grafana_url.with_path("api/datasources")
    datasource = requests.get(
        api_url.human_repr(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {grafana_token}",
        },
    )

    # Get the cost-monitoring yesoreyeram-infinity-datasource UID
    datasource_uid = datasource.json()[1]["uid"]
    target_url = URL("http://jupyterhub-cost-monitoring.support.svc.cluster.local")
    # See https://jupyterhub-cost-monitoring.readthedocs.io/en/latest/api/ for available endpoints
    subpath = "total-costs"

    headers = {
        "Authorization": f"Bearer {grafana_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "queries": [
            {
                "datasource": {
                    "type": "yesoreyeram-infinity-datasource",
                    "uid": datasource_uid,
                },
                "url": str(target_url / subpath),
                "url_options": {
                    "method": "GET",
                    "data": "",
                },
                "type": "json",
                "source": "url",
                "format": "table",
                "parser": "backend",
                "root_selector": "",
                # Columns can change depending on data returned by endpoint – see https://github.com/2i2c-org/jupyterhub-cost-monitoring/blob/a6e49c719e8600fc2490e2fb2a77da09ce4bcd1a/dashboards/common.libsonnet#L128 for examples from existing cloud cost grafana dashboards
                "columns": [
                    {"selector": "date", "text": "Date", "type": "timestamp"},
                    {"selector": "name", "text": "Name", "type": "string"},
                    {"selector": "cost", "text": "Cost", "type": "number"},
                ],
            }
        ],
        "from": "now-1d",
        "to": "now",
    }

    # https://grafana.com/docs/grafana-cloud/developer-resources/api-reference/http-api/data_source/#query-a-data-source
    query_url = grafana_url.with_path("api/ds/query")

    response = requests.post(
        query_url.human_repr(), headers=headers, data=json.dumps(payload)
    )

    if response.status_code == 200:
        return True
    else:
        print(f"{response.status_code}: {response.reason}")
        return False


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
        else:
            cost_tags_active = check_cost_data(cluster_name)
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
df.to_csv("../docs/topic/monitoring-alerting/cost-monitoring.csv", index=False)
