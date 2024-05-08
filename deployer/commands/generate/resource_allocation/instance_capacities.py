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


def get_running_instance_types():
    """
    Returns a unique list of the k8s cluster's running nodes' instance types.
    """
    output = subprocess.check_output(
        [
            "kubectl",
            "get",
            "node",
            r"--output=jsonpath-as-json={.items[*].metadata.labels['node\.kubernetes\.io/instance-type']}",
        ],
        text=True,
    )
    instance_types = list(set(json.loads(output)))
    return instance_types


def get_instance_capacity(instance_type: str):
    """
    Returns a dictionary summarizing total and allocatable capacity of
    cpu/memory for an instance type by inspecting one in the k8s cluster.
    """
    output = subprocess.check_output(
        [
            "kubectl",
            "get",
            "node",
            "--output=jsonpath-as-json={.items[*].status}",
            f"--selector=node.kubernetes.io/instance-type={instance_type}",
        ],
        text=True,
    )

    # all nodes of a given instance type should report the same capacity and
    # allocatable cpu/memory, we just pick one
    status = json.loads(output)[0]

    cpu_capacity = float(parse_quantity(status["capacity"]["cpu"]))
    cpu_allocatable = float(parse_quantity(status["allocatable"]["cpu"]))
    mem_capacity = int(parse_quantity(status["capacity"]["memory"]))
    mem_allocatable = int(parse_quantity(status["allocatable"]["memory"]))

    # format memory to use Gi with 3 decimal places
    mem_capacity = str(math.floor(mem_capacity / 1024**3 * 1000) / 1000) + "Gi"
    mem_allocatable = str(math.floor(mem_allocatable / 1024**3 * 1000) / 1000) + "Gi"

    info = {
        "cpu_capacity_low": cpu_capacity,
        "cpu_capacity_high": cpu_capacity,
        "cpu_allocatable_low": cpu_allocatable,
        "cpu_allocatable_high": cpu_allocatable,
        "mem_capacity_low": mem_capacity,
        "mem_capacity_high": mem_capacity,
        "mem_allocatable_low": mem_allocatable,
        "mem_allocatable_high": mem_allocatable,
    }
    return info


def get_instance_capacities():
    """
    Returns a dictionary with entries for each of the k8s cluster's running
    instance types.
    """
    instance_types = get_running_instance_types()

    info = {}
    for it in instance_types:
        info[it] = get_instance_capacity(it)
    return info


@resource_allocation_app.command()
def instance_capacities(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
):
    """
    Updates `instance_capacities.yaml` with an individual cluster's running
    instance types' total and allocatable capacity.

    To run this command for all clusters, `xargs` can be used like this:

        deployer config get-clusters | xargs -I {} deployer generate resource-allocation instance-capacities {}
    """
    file_path = HERE / "instance_capacities.yaml"
    file_path.touch(exist_ok=True)

    # acquire a Cluster object
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    # auth and inspect cluster
    with cluster.auth():
        new_ics = get_instance_capacities()

    # read
    with open(file_path) as f:
        ics = yaml.load(f) or {}

    # update
    for type, new_cap in new_ics.items():
        cap = ics.get(type)

        # add new entry
        if not cap:
            ics[type] = new_cap
            continue

        # update existing entry, comparing and updating the lowest low and
        # highest high for the kind of resources
        props = ["cpu_capacity", "cpu_allocatable", "mem_capacity", "mem_allocatable"]
        for p in props:
            lp = f"{p}_low"
            if parse_quantity(new_cap[lp]) < parse_quantity(cap[lp]):
                cap[lp] = new_cap[lp]
        for p in props:
            lp = f"{p}_high"
            if parse_quantity(new_cap[lp]) > parse_quantity(cap[lp]):
                cap[lp] = new_cap[lp]

    # write
    with open(file_path, "w") as f:
        yaml.dump(ics, f)
