import json
import math
import subprocess
from pathlib import Path

import typer
from kubernetes.utils.quantity import parse_quantity
from ruamel.yaml import YAML

from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import find_absolute_path_to_cluster_file

from .resource_allocation_app import resource_allocation_app

HERE = Path(__file__).parent
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


def get_k8s_distribution():
    """
    Returns a 2-tuple with the guessed the k8s distribution based on the k8s
    api-server's reported version, either Google's GKE, Amazon's EKS, or Azure's
    AKS, and the server's reported gitVersion.
    """
    output = subprocess.check_output(
        [
            "kubectl",
            "version",
            "--output=json",
        ],
        text=True,
    )
    version_info = json.loads(output)
    server_version_info = version_info["serverVersion"]["gitVersion"]
    if "gke" in server_version_info:
        return "gke", server_version_info
    if "eks" in server_version_info:
        return "eks", server_version_info
    return "aks", server_version_info


def get_daemon_sets_requests():
    """
    Returns a list of dicts with info about DaemonSets with pods desired to be scheduled on
    some nodes the k8s cluster.
    """
    output = subprocess.check_output(
        [
            "kubectl",
            "get",
            "ds",
            "--all-namespaces",
            "--output=jsonpath-as-json={.items[*]}",
        ],
        text=True,
    )
    daemon_sets = json.loads(output)

    # filter out DaemonSets that aren't desired on any node
    daemon_sets = [ds for ds in daemon_sets if ds["status"]["desiredNumberScheduled"]]

    info = []
    for ds in daemon_sets:
        name = ds["metadata"]["name"]
        req_mem = req_cpu = lim_mem = lim_cpu = 0
        for c in ds["spec"]["template"]["spec"]["containers"]:
            resources = c.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})
            req_mem += parse_quantity(requests.get("memory", 0))
            lim_mem += parse_quantity(limits.get("memory", 0))
            req_cpu += parse_quantity(requests.get("cpu", 0))
            lim_cpu += parse_quantity(limits.get("cpu", 0))

        info.append(
            {
                "name": name,
                "cpu_request": float(req_cpu),
                "cpu_limit": float(lim_cpu),
                "memory_request": int(req_mem),
                "memory_limit": int(lim_mem),
            }
        )

    return info


def get_daemon_sets_overhead():
    """
    Returns a summary of the overhead from get_daemon_sets_requests.
    """
    daemon_sets = get_daemon_sets_requests()
    # filter out DaemonSets related to nvidia GPUs
    daemon_sets = [ds for ds in daemon_sets if "nvidia" not in ds["name"]]
    # separate DaemonSets without requests, as only requests are what impacts
    # scheduling of pods and reduces a node's remaining allocatable resources
    req_daemon_sets = [
        ds for ds in daemon_sets if ds["cpu_request"] or ds["memory_request"]
    ]
    other_daemon_sets = [
        ds for ds in daemon_sets if not ds["cpu_request"] and not ds["memory_request"]
    ]

    cpu_requests = sum([ds["cpu_request"] for ds in req_daemon_sets])
    memory_requests = sum([ds["memory_request"] for ds in req_daemon_sets])
    info = {
        "requesting_daemon_sets": ",".join(
            sorted([ds["name"] for ds in req_daemon_sets])
        ),
        "other_daemon_sets": ",".join(sorted([ds["name"] for ds in other_daemon_sets])),
        "cpu_requests": str(math.ceil(cpu_requests * 1000)) + "m",
        "memory_requests": str(math.ceil(memory_requests / 1024**2)) + "Mi",
    }
    return info


@resource_allocation_app.command()
def daemonset_overhead(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
):
    """
    Updates `daemonset_overhead.yaml` with an individual cluster's DaemonSets
    with running pods combined requests of CPU and memory, excluding GPU related
    DaemonSets.
    """
    file_path = HERE / "daemonset_overhead.yaml"
    file_path.touch(exist_ok=True)

    # acquire a Cluster object
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    # auth and inspect cluster
    with cluster.auth():
        k8s_dist, k8s_version = get_k8s_distribution()
        ds_overhead = get_daemon_sets_overhead()

    # read
    with open(file_path) as f:
        info = yaml.load(f) or {}

    # update
    ds_overhead["k8s_version"] = k8s_version
    info.setdefault(k8s_dist, {})[cluster_name] = ds_overhead

    # write
    with open(file_path, "w") as f:
        yaml.dump(info, f)
