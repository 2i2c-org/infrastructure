import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from dateutil.parser import parse
from kubernetes.utils.quantity import parse_quantity
from ruamel.yaml import YAML

from .resource_allocation_app import resource_allocation_app

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
                # Let's make sure we don't accidentally pick up a core node
                f"node.kubernetes.io/instance-type={instance_type},hub.jupyter.org/node-purpose=user",
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

    # Let's just make sure it is at least 3 minutes old, to give all pods a
    # chance to actually schedule on this.
    nodes["items"] = [
        n
        for n in nodes["items"]
        if datetime.now(timezone.utc) - parse(n["metadata"]["creationTimestamp"])
        > timedelta(minutes=3)
    ]

    if not nodes.get("items"):
        # A node was found, but it was not old enough.
        # We want to wait a while before using it, so daemonsets get time to
        # be scheduled
        raise ValueError(
            f"Node with instance-type={instance_type} found in current kubernetes cluster is not 3 minutes old yet. Wait and try again"
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
    # and pods running on the kubernetes cluster.
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
        # From https://kubernetes.io/docs/concepts/workloads/pods/init-containers/#resource-sharing-within-containers
        # > - The highest of any particular resource request or limit defined on
        # >   all init containers is the effective init request/limit. If any
        # >   resource has no resource limit specified this is considered as the
        # >   highest limit.
        # > - The Pod's effective request/limit for a resource is the higher of:
        # >  - the sum of all app containers request/limit for a resource
        # >  - the effective init request/limit for a resource
        #
        # So we have to calculate the requests of the init containers and containers separately,
        # and take the max as the effective request / limit
        container_cpu_request = container_mem_request = 0
        init_container_cpu_request = init_container_mem_request = 0

        for c in p["spec"]["containers"]:
            container_mem_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("memory", "0")
            )
            container_cpu_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("cpu", "0")
            )

        for c in p["spec"].get("initContainers", []):
            init_container_mem_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("memory", "0")
            )
            init_container_cpu_request += parse_quantity(
                c.get("resources", {}).get("requests", {}).get("cpu", "0")
            )

        print(
            p["metadata"]["name"],
            max(init_container_mem_request, container_mem_request),
        )
        cpu_available -= max(container_cpu_request, init_container_cpu_request)
        mem_available -= max(container_mem_request, init_container_mem_request)

    return {
        # CPU units are  in fractions, while memory units are bytes
        "capacity": {"cpu": float(cpu_capacity), "memory": int(mem_capacity)},
        "allocatable": {"cpu": float(cpu_allocatable), "memory": int(mem_allocatable)},
        "measured_overhead": {
            "cpu": float(cpu_allocatable - cpu_available),
            "memory": int(mem_allocatable - mem_available),
        },
        "available": {"cpu": float(cpu_available), "memory": int(mem_available)},
    }


@resource_allocation_app.command()
def node_info_update(
    instance_type: str = typer.Argument(
        ..., help="Instance type to generate Resource Allocation options for"
    ),
):
    """
    Generates a new entry holding info about the capacity of a node of a certain instance type
    or updates an existing one that is then used to update a json file called `node-capacity-info.json`.
    This file is then used for generating the resource choices.
    """
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
