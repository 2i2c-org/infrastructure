import json
import subprocess
from pathlib import Path

import typer
from kubernetes.utils.quantity import parse_quantity
from ruamel.yaml import YAML

from ..cli_app import app

HERE = Path(__file__).parent

yaml = YAML(typ="rt")


def get_node_capacity_info(instance_type: str):
    # Get full YAML spec of all nodes with this instance_type
    nodes = json.loads(
        subprocess.check_output(
            [
                "kubectl",
                "get",
                "node",
                "-l",
                f"node.kubernetes.io/instance-type={instance_type}",
                "-o",
                "json",
            ]
        ).decode()
    )

    if not nodes.get("items"):
        # No nodes with given instance_type found!
        # A node with this instance_type needs to be actively running for us to accurately
        # calculate how much resources are available, as it relies on the non-jupyter pods
        # running at that time.
        raise ValueError(
            f"No nodes with instance-type={instance_type} found in current kubernetes cluster"
        )

    # Just pick one node
    node = nodes["items"][0]

    # This is the toal amount of RAM and CPU on the node.
    capacity = node["status"]["capacity"]
    cpu_capacity = parse_quantity(capacity["cpu"])
    mem_capacity = parse_quantity(capacity["memory"])

    # Total amount of RAM and CPU available to kubernetes as a whole.
    # This accounts for things running on the node, such as kubelet, the
    # container runtime, systemd, etc. This does *not* count for daemonsets
    # and pods runninng on the kubernetes cluster.
    allocatable = node["status"]["allocatable"]
    cpu_allocatable = parse_quantity(allocatable["cpu"])
    mem_allocatable = parse_quantity(allocatable["memory"])

    # Find all pods running on this node
    all_pods = json.loads(
        subprocess.check_output(
            [
                "kubectl",
                "get",
                "pod",
                "-A",
                "--field-selector",
                f'spec.nodeName={node["metadata"]["name"]}',
                "-o",
                "json",
            ]
        ).decode()
    )["items"]

    # Filter out jupyterhub user pods
    # TODO: Filter out dask scheduler and worker pods
    pods = [
        p
        for p in all_pods
        if p["metadata"]["labels"].get("component") not in ("singleuser-server",)
    ]

    # This is the amount of resources available for our workloads - jupyter and dask.
    # We start with the allocatable resources, and subtract the resource *requirements*
    # for all the pods that are running on every node, primarily from kube-system and
    # support. The amount left over is what is available for the *scheduler* to put user pods
    # on to.
    cpu_available = cpu_allocatable
    mem_available = mem_allocatable

    for p in pods:
        mem_request = 0
        cpu_request = 0
        # Iterate through all the containers in the pod, and count the memory & cpu requests
        # they make. We don't count initContainers' requests as they don't overlap with the
        # container requests at any point.
        for c in p["spec"]["containers"]:
            mem_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("memory", "0")
            )
            cpu_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("cpu", "0")
            )
        cpu_available -= cpu_request
        mem_available -= mem_request

    return {
        # CPU units are  in fractions, while memory units are bytes
        "capacity": {"cpu": float(cpu_capacity), "memory": int(mem_capacity)},
        "available": {"cpu": float(cpu_available), "memory": int(mem_available)},
    }


@app.command()
def update_node_capacity_info(
    instance_type: str = typer.Argument(
        ..., help="Instance type to generate Resource Allocation options for"
    ),
):
    try:
        with open(HERE / "node-capacity-info.json") as f:
            instances_info = json.load(f)
    except FileNotFoundError:
        instances_info = {}
    node_capacity = get_node_capacity_info(instance_type)

    instances_info[instance_type] = node_capacity
    with open(HERE / "node-capacity-info.json", "w") as f:
        json.dump(instances_info, f, indent=4)

    print(f"Updated node-capacity-info.json for {instance_type}")
