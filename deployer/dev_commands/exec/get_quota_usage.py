import json
import re
import subprocess
import sys

import typer
from ruamel.yaml import YAML

from deployer.cli_app import exec_app
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.infra_components.cluster import Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


def get_nfs_pod_name(namespace: str):
    # Get full YAML spec of all nodes with this instance_type
    pods = json.loads(
        subprocess.check_output(
            [
                "kubectl",
                "get",
                "pod",
                "-l",
                "app.kubernetes.io/component=nfs-server",
                "-n",
                namespace,
                "-o",
                "json",
            ]
        ).decode()
    )

    if not pods.get("items"):
        # No nodes with given instance_type found!
        # A node with this instance_type needs to be actively running for us to accurately
        # calculate how much resources are available, as it relies on the non-jupyter pods
        # running at that time.
        raise ValueError(f"No pods with nfs-server label running on {namespace}")

    assert len(pods["items"]) == 1

    pod = pods["items"][0]
    return pod["metadata"]["name"]


# Verbose pattern
LINE_PATTERN_TEMPLATE = r"""
^
/export/{hub_name}/(?P<name>.*\S)\s+
# used
(?P<used>\d+)\s+
# soft
(\d+)\s+
# hard
(\d+)\s+
# warn
(\d+)\s+
# grace
\[-*\]
$
"""


def get_quota_usage_impl(hub_name: str, nfs_pod_name: str):
    # Get full YAML spec of all nodes with this instance_type
    quota_lines = (
        subprocess.check_output(
            [
                # Pull entries from NFS pod
                "kubectl",
                "exec",
                "-n",
                hub_name,
                nfs_pod_name,
                "-c",
                "enforce-xfs-quota",
                "--",
                "xfs_quota",
                "-x",
                "-c",
                "report -N -p -b",
                "-D",
                f"/export/{hub_name}/.projects",
                "-P",
                f"/export/{hub_name}/.projid",
                "/export",
            ]
        )
        .decode()
        .splitlines()
    )

    # Find the qutoas for each line
    line_pattern = LINE_PATTERN_TEMPLATE.format(hub_name=hub_name)
    return {
        match["name"]:
        # Reported usage is in KiB
        int(match["used"]) * 1024
        for line in quota_lines
        # Only take matching lines
        if (match := re.match(line_pattern, line, flags=re.X))
    }


@exec_app.command()
def get_quota_usage(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    output_json: bool = typer.Option(
        False, "--json", help="Output JSON rather than pretty table"
    ),
):
    """
    Determine usage of storage quotas on a hub"""
    validate_cluster_config(cluster_name)
    cluster = Cluster.from_name(cluster_name)

    with cluster.auth(silent=True):
        pod_name = get_nfs_pod_name(hub_name)
        quotas = get_quota_usage_impl(hub_name, pod_name)

    if output_json:
        json.dump(quotas, sys.stdout, indent=4, sort_keys=True)
    else:
        for key, value in quotas.items():
            print(f"{key}:{value}")
