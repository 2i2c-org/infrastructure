"""
Script to update data used in `docs/topic/monitoring-alerting/cost-monitoring-availability.md`
"""

import asyncio
from pathlib import Path

import pandas as pd
from ruamel.yaml import YAML

from deployer.dev_commands.exec.cost_monitoring.cost_monitoring_app import query
from docs.helper_programs.hub_info_table import get_cluster_grafana_url
from docs.helper_programs.utils import get_cluster_provider, get_clusters_list

yaml = YAML(typ="safe", pure=True)


async def main():
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
                response = await asyncio.to_thread(
                    query, cluster_name, "total-costs", verbose=False
                )
                if response.status_code == 200:
                    cost_tags_active = True
                else:
                    print(f"{cluster_name} – {response.status_code}: {response.reason}")
                    cost_tags_active = False
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
    filename = Path(__file__).parent.parent.joinpath(
        "docs", "csv", "cost-monitoring.txt"
    )
    # mystmd's csv-table can't read a .csv file, so wrap the CSV in the directive
    # and let the docs {include} this file.
    # ref: https://github.com/jupyter-book/mystmd/issues/2573
    filename.write_text(
        f"```{{csv-table}}\n:header-rows: 1\n\n{df.to_csv(index=False)}```\n"
    )
    print(f"Saved table to {filename}")


if __name__ == "__main__":
    asyncio.run(main())
