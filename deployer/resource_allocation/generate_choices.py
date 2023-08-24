import json
import sys
from enum import Enum
from pathlib import Path

import typer
from ruamel.yaml import YAML

from ..cli_app import app

yaml = YAML(typ="rt")

HERE = Path(__file__).parent


class ResourceAllocationStrategies(str, Enum):
    PROPORTIONAL_MEMORY_STRATEGY = "proportional-memory-strategy"


def proportional_memory_strategy(nodeinfo: dict, num_allocations: int):
    """
    Generate choices for resource allocation based on proportional changes to memory

    Used primarily in research cases where:
    1. Workloads are more memory constrained than CPU constrained
    2. End users can be expected to select appropriate amount of memory they need for a given
       workload, either by their own intrinsic knowledge or instructed by an instructor.

    It features:
    1. No memory overcommit at all, as end users are expected to ask for as much memory as
       they need.
    2. CPU *guarantees* are proportional to amount of memory guarantee - the more memory you
       ask for, the more CPU you are guaranteed. This allows end users to pick resources purely
       based on memory only, simplifying the mental model. Also allows for maximum packing of
       user pods onto a node, as we will *not* run out of CPU on a node before running out of
       memory.
    3. No CPU limits at all, as CPU is a more flexible resource. The CPU guarantee will ensure
       that users will not be starved of CPU.
    4. Each choice the user can make approximately has half as many resources as the next largest
       choice, with the largest being a full node. This offers a decent compromise - if you pick
       the largest option, you will most likely have to wait for a full node spawn, while smaller
       options are much more likely to be shared.
    """

    # We operate on *available* memory, which already accounts for system components (like kubelet & systemd)
    # as well as daemonsets we run on every node. This represents the resources that are available
    # for user pods.
    available_node_mem = nodeinfo["available"]["memory"]
    available_node_cpu = nodeinfo["available"]["cpu"]

    # We always start from the top, and provide a choice that takes up the whole node.
    mem_limit = available_node_mem

    choices = {}
    for i in range(num_allocations):
        # CPU guarantee is proportional to the memory limit for this particular choice.
        # This makes sure we utilize all the memory on a node all the time.
        cpu_guarantee = (mem_limit / available_node_mem) * available_node_cpu

        # Memory is in bytes, let's convert it to GB to display
        mem_display = mem_limit / 1024 / 1024 / 1024
        display_name = f"{mem_display:.1f} GB RAM"

        choice = {
            "display_name": display_name,
            "kubespawner_override": {
                # Guarantee and Limit are the same - this strategy has no oversubscription
                "mem_guarantee": int(mem_limit),
                "mem_limit": int(mem_limit),
                "cpu_guarantee": cpu_guarantee,
                # CPU limit is set to entire available CPU of the node, making sure no single
                # user can starve the node of critical kubelet / systemd resources.
                # Leaving it unset sets it to same as guarantee, which we do not want.
                "cpu_limit": available_node_cpu,
            },
        }
        choices[f"mem_{num_allocations - i}"] = choice

        # Halve the mem_limit for the next choice
        mem_limit = mem_limit / 2

    # Reverse the choices so the smallest one is first
    choices = dict(reversed(choices.items()))

    # Make the smallest choice the default explicitly
    choices[list(choices.keys())[0]]["default"] = True

    return choices


@app.command()
def generate_resource_allocation_choices(
    instance_type: str = typer.Argument(
        ..., help="Instance type to generate Resource Allocation options for"
    ),
    num_allocations: int = typer.Option(5, help="Number of choices to generate"),
    strategy: ResourceAllocationStrategies = typer.Option(
        ResourceAllocationStrategies.PROPORTIONAL_MEMORY_STRATEGY,
        help="Strategy to use for generating resource allocation choices choices",
    ),
):
    with open(HERE / "node-capacity-info.json") as f:
        nodeinfo = json.load(f)

    if instance_type not in nodeinfo:
        print(
            f"Capacity information about {instance_type} not available", file=sys.stderr
        )
        print("TODO: Provide information on how to update it", file=sys.stderr)
        sys.exit(1)

    # Call appropriate function based on what strategy we want to use
    if strategy == ResourceAllocationStrategies.PROPORTIONAL_MEMORY_STRATEGY:
        choices = proportional_memory_strategy(nodeinfo[instance_type], num_allocations)
    else:
        raise ValueError(f"Strategy {strategy} is not currently supported")
    yaml.dump(choices, sys.stdout)
