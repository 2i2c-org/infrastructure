import json

import requests
import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML
from yarl import URL

from deployer.cli_app import exec_app
from deployer.infra_components.cluster import Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@exec_app.command()
def promql(
    query: str = typer.Argument(help="PromQL query to execute"),
    cluster_name: str = typer.Argument(help="Name of the Cluster to Query"),
    output_json: bool = typer.Option(
        False, "--json", help="Output JSON rather than pretty table"
    ),
):
    """
    Execute a PromQL query against a cluster's prometheus instance
    """

    cluster = Cluster.from_name(cluster_name)

    promql_api = URL(f"{cluster.get_external_prometheus_url()}/api/v1/query")

    query_api = promql_api.with_query({"query": query})

    resp = requests.get(str(query_api), auth=cluster.get_cluster_prometheus_creds())
    resp.raise_for_status()

    result = resp.json()["data"]["result"]

    if output_json:
        data = []
        for entry in result:
            row = entry["metric"].copy()
            row["value"] = entry["value"][1]
            data.append(row)

        print(json.dumps(data))
    else:
        if len(result) == 0:
            print("No data returned")
            return

        column_names = list(result[0]["metric"].keys())

        table = Table()
        for cn in column_names:
            table.add_column(cn, justify="left")
        table.add_column("value", justify="right", no_wrap=True)

        for entry in result:
            row = []
            for cn in column_names:
                row.append(entry["metric"][cn])
            row.append(entry["value"][1])
            table.add_row(*row)

        Console().print(table)
