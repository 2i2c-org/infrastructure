import calendar
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional

import requests
import typer
from rich import progress
from rich.live import Live
from rich.table import Table
from yarl import URL

from deployer.app import generate_app
from deployer.infra_components.cluster import Cluster

# Usernames to ignore when calculating MAU
USERNAMES_TO_IGNORE = {
    "deployment-service-check",
    # 2i2c staff GitHub IDs
    "agoose77",
    "choldgraf",
    "colliand",
    "GeorgianaElena",
    "Gman0909",
    "haroldcampbell",
    "jnywong",
    "yuvipanda",
    "jmunroe",
    # 2i2c staff google ids
    "ahollands@2i2c.org",
    "choldgraf@2i2c.org",
    "colliand@2i2c.org",
    "georgianaelena@2i2c.org",
    "gmaciocci@2i2c.org",
    "hcampbell@2i2c.org",
    "jwong@2i2c.org",
    "yuvipanda@2i2c.org",
    "jmunroe@2i2c.org",
}


@generate_app.command()
def mau(
    month: str = typer.Argument(help="Month to generate MAU data for"),
    cluster_name: Optional[str] = typer.Option(
        None, help="Restrict to just one cluster"
    ),
    csv_file: Annotated[
        Path | None, typer.Option(help="Output data to csv file at this path")
    ] = None,
):
    """
    Generate MAU for all (or some) clusters for a given month
    """
    if cluster_name:
        clusters = [Cluster.from_name(cluster_name)]
    else:
        clusters = Cluster.get_all()

    cluster_activity: dict[str, int] = {}

    table = Table()
    table.add_column("Cluster")
    table.add_column("MAU")

    with Live(table) as live:
        progress_bar = progress.Progress(console=live.console)
        progress_bar.start()
        clusters_progress = progress_bar.add_task("Clusters", total=len(clusters))
        dates_progress = progress_bar.add_task("Days")

        for cluster in clusters:
            progress_bar.update(
                clusters_progress,
                description=f"Processing {cluster.spec['name']}",
                advance=1,
            )
            promql_api = URL(
                f"{cluster.get_external_prometheus_url()}/api/v1/query_range"
            )

            time_parts = month.split("-", 2)

            # Explicitly construct the datetime as UTC, so we get standardized MAU for all our clusters
            start_date = datetime(
                int(time_parts[0]), int(time_parts[1]), 1, tzinfo=timezone.utc
            )

            # Get all pods that start with jupyter-.*, and treat them as user servers.
            # We could join with kube_pod_labels for a more accurate version of this.
            # We can't use the username in the pod label because it is escaped, and we won't
            # get the full username for filtering.
            query = """
            max(
                kube_pod_annotations{pod=~"jupyter-.*"}
            )
            by (annotation_hub_jupyter_org_username)
            """

            # Users mapped to how many minutes their server was active this month
            user_activity: dict[str, int] = {}

            days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
            progress_bar.update(dates_progress, total=days_in_month)

            prometheus_creds = cluster.get_cluster_prometheus_creds()
            for i in range(days_in_month):
                # Start time and End time are inclusive, so we want time from 00:00:00 to 23:59:59
                start_time = start_date + timedelta(days=i)
                end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

                progress_bar.update(
                    dates_progress,
                    completed=i,
                    description=f"Processing {start_time.strftime('%Y-%m-%d')}",
                )
                params = {
                    "query": query,
                    "start": int(start_time.timestamp()),
                    "end": int(end_time.timestamp()),
                    "step": "1m",
                }

                query_api = promql_api.with_query(params)

                resp = requests.get(str(query_api), auth=prometheus_creds)
                resp.raise_for_status()

                result = resp.json()["data"]["result"]
                for row in result:
                    username = row["metric"]["annotation_hub_jupyter_org_username"]

                    if username in USERNAMES_TO_IGNORE:
                        continue

                    # Since "step" is 1m, each value that is present indicates this pod was present
                    # for that minute. So the total number of values present indicates how long the
                    # user was active.
                    minutes_active = len(row["values"])
                    user_activity[username] = (
                        user_activity.get(username, 0) + minutes_active
                    )
            cluster_activity[cluster.spec["name"]] = len(user_activity)

            table.add_row(cluster.spec["name"], str(len(user_activity)))

    if csv_file:
        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(("cluster_name", "mau"))
            for name, active_users in cluster_activity.items():
                writer.writerow((name, str(active_users)))
