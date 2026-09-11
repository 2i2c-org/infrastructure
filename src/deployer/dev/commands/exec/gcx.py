import os
import subprocess

import typer
from ....infra_components.cluster import Cluster
from deployer.dev.app import exec_app


@exec_app.command()
def gcx(
    cluster_name: str = typer.Argument("Name of cluster whose grafana we target"),
    gcx_command: list[str] = typer.Argument("GCX command to execute")
):
    """
    Execute arbitrary grafana control (gcx) commands against a particular grafana
    """
    cluster = Cluster.from_name(cluster_name)

    env = os.environ.copy()
    env["GRAFANA_TOKEN"] = cluster.get_grafana_token()
    env["GRAFANA_SERVER"] = cluster.get_grafana_url()
    env["GRAFANA_ORG_ID"] = "1"  # The default 'main' org

    subprocess.check_call(["gcx"] + gcx_command, env=env)
