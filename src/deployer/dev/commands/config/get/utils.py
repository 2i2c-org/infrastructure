from collections import defaultdict
from typing import Any

from rich.table import Table


def turn_data_into_table(title, columns, highlight_idx, threshold, data) -> Any:
    table = Table(title=title, header_style="bold cyan")

    for idx, col in enumerate(columns):
        if idx != highlight_idx:
            table.add_column(col, style="white", no_wrap=True)
        else:
            table.add_column(col, style="green", justify="right")

    for cluster, hubs in sorted(data.items()):
        for hub, version in sorted(hubs.items()):
            version_style = "bold yellow" if version != threshold else "green"
            table.add_row(cluster, hub, f"[{version_style}]{version}[/]")

    return table


def merge_version_dicts(
    *version_dicts: dict[str, dict[str, str]],
    metric_names: list[str],
) -> dict[str, Any]:
    """
    Merge N version dicts into a JSON-friendly structure:

    {
      "clusters": [
        {
          "name": "earthscope",
          "hubs": [
            {
              "name": "staging",
              "versions": {
                "k8s": "1.34",
                "z2jh": "4.3.3",
                "dask": "2024.8.1"
              }
            },
            ...
          ]
        },
        ...
      ]
    }

    version_dicts: sequence of {cluster: {hub: version}} dicts
    metric_names: list of metric names in the same order, e.g. ["k8s", "z2jh", "dask"]
    """
    if len(version_dicts) != len(metric_names):
        raise ValueError("version_dicts and metric_names must have the same length")

    all_clusters = set()
    for d in version_dicts:
        all_clusters |= set(d.keys())

    result_clusters = []
    for cluster in sorted(all_clusters):
        hubs_map = defaultdict(dict)

        for d, metric in zip(version_dicts, metric_names):
            for hub, version in d.get(cluster, {}).items():
                hubs_map[hub][metric] = version

        hubs_list = [
            {"name": hub, "versions": hubs_map[hub]} for hub in sorted(hubs_map.keys())
        ]

        result_clusters.append(
            {
                "name": cluster,
                "hubs": hubs_list,
            }
        )

    return {"clusters": result_clusters}


def render_versions_table(data: dict[str, Any]) -> Table:
    """
    Render merged version data as a Rich table.
    Columns: Cluster, Hub, <metric1>, <metric2>, ...
    """
    clusters = data["clusters"]
    if not clusters:
        return Table(title="No clusters found")

    metrics = set()
    for c in clusters:
        for h in c["hubs"]:
            metrics |= set(h["versions"].keys())
    metrics = sorted(metrics)

    table = Table(title="Cluster versions", header_style="bold white")
    table.add_column("Cluster", style="cyan", no_wrap=True)
    table.add_column("Hub", style="white", no_wrap=True)
    for m in metrics:
        table.add_column(m.capitalize(), style="white", justify="right")

    for c in clusters:
        for h in c["hubs"]:
            row = [c["name"], h["name"]] + [h["versions"].get(m, "-") for m in metrics]
            table.add_row(*row)

    return table
