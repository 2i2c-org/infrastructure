import gzip
import io
import json
import re
import shlex
import subprocess
from datetime import datetime, timedelta, timezone

import requests
import tenacity
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


@exec_app.command()
def prom_openmetrics_dump(
    metric_name: str = typer.Argument(help="Prometheus metric to execute"),
    output_path: str = typer.Argument(
        help="Path to output gzip compressed openmetrics file to"
    ),
    cluster_name: str = typer.Argument("Cluster to dump metrics from"),
    keep_label: list[str] = typer.Option(),
):
    """
    Dump a prometheus metric from a cluster in openmetrics format
    """

    def process_metric_line(
        openmetrics_line: str, keep_labels: list[str], add_labels: dict[str, str]
    ) -> str:
        try:
            # Small enough parser for just the stuff we need
            # https://github.com/prometheus/OpenMetrics/blob/main/specification/OpenMetrics.md#abnf
            # has useful parser definition we can refer to
            metric, value, ts = openmetrics_line.rsplit(" ", 3)
            # FIXME: This doesn't handle it fine when there are quotes or newlines in label values!
            labels = dict(re.findall(r"(\w+)=\"(.*?)\",?", metric))
            metric_name = metric.split("{")[0]

            kept_labels = {k: v for k, v in labels.items() if k in keep_labels}
            kept_labels.update(add_labels)

            # FIXME: This doesn't handle it fine when there are quotes or newlines in label values!
            constructed_labels = ",".join(f'{k}="{v}"' for k, v in kept_labels.items())
            constructed_metric = f"{metric_name}{{{constructed_labels}}}"
        except Exception as e:
            print(openmetrics_line)

        return f"{constructed_metric} {value} {ts}"

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5), wait=tenacity.wait_random(1, 60)
    )
    def dump_metrics(
        pod_name: str, start_time: datetime, end_time: datetime
    ) -> list[str]:
        """
        Dump required metrics from the given prometheus pod, from start_time to end_time

        This is a function so we can have automatic retries easily, as we do run into network
        related breakage often. Retrying is the right call in almost all cases.
        """
        print(
            f"Processing {cluster.spec['name']} from {start_time.isoformat()} to {end_time.isoformat()}...",
            end="",
        )
        cmd = (
            [
                "kubectl",
                "-n",
                "support",
                "exec",
                pod_name,
                "-c",
                "prometheus-server",
                "--",
            ]
            + tsdb_dump_cmd
            + [
                "--min-time",
                str(int(start_time.timestamp() * 1000)),
                "--max-time",
                str(int(end_time.timestamp() * 1000)),
            ]
        )
        # import shlex
        # print(shlex.join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        lines = []
        eof_reached = False
        for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
            if line.startswith("# EOF"):
                # We skip EOF markers but note them as present so we know if we got everything
                eof_reached = True
                continue
            # This may raise exceptions if we get a partial line, which will trigger retries
            lines.append(
                process_metric_line(line, keep_label, {"cluster": cluster.spec["name"]})
            )
        proc.wait()
        if not eof_reached:
            # Raising this as an exception triggers our retry behavior, which is what we want
            print("Failed due to missing EOF")
            raise Exception(
                f"Didn't find EOF for {cluster.spec['name']} from {start_time} to {end_time}, with command {shlex.join(cmd)}"
            )
        print(f" Processed {len(lines)} lines")
        return lines

    tsdb_dump_cmd = [
        "promtool",
        "tsdb",
        "dump-openmetrics",
        "/data",
        f'--match={{__name__="{metric_name}"}}',
    ]

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        cluster = Cluster.from_name(cluster_name)
        with cluster.auth():
            pod_name = (
                subprocess.check_output(
                    [
                        "kubectl",
                        "-n",
                        "support",
                        "get",
                        "pod",
                        "-o",
                        "name",
                        "-l",
                        "app.kubernetes.io/name=prometheus,app.kubernetes.io/component=server",
                    ]
                )
                .decode()
                .strip()
            )
            # We want to dump out metrics roughly a month at a time, to reduce the
            # load on the prometheus server, and to make sure we actually get all our
            # metrics
            now = datetime.now(timezone.utc)
            time_ranges: list[tuple[datetime, datetime]] = []
            for i in range(36):
                time_ranges.append(
                    (now - timedelta(days=30 * (i + 1)), now - timedelta(days=30 * i))
                )

            for start_time, end_time in time_ranges:
                lines = dump_metrics(pod_name, start_time, end_time)
                for line in lines:
                    f.write(line)
            f.write("#EOF")
