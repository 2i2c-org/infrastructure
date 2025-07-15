import json
import math
import sys
from enum import Enum
from pathlib import Path
from typing import List

import typer
from ruamel.yaml import YAML

from .resource_allocation_app import resource_allocation_app

yaml = YAML(typ="rt")

HERE = Path(__file__).parent


class ResourceAllocationStrategies(str, Enum):
    PROPORTIONAL_MEMORY_STRATEGY = "proportional-memory-strategy"


def proportional_memory_strategy(
    instance_type: str, nodeinfo: dict, num_allocations: int
):
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
    # In addition, we provide some wiggle room to account for additional daemonset requests or other
    # issues that may pop up due to changes outside our control (like k8s upgrades). This is either
    # 2% of the available capacity, or 2GB / 1 CPU (whichever is smaller)
    mem_overhead_wiggle = min(
        nodeinfo["available"]["memory"] * 0.02, 2 * 1024 * 1024 * 1024
    )
    cpu_overhead_wiggle = min(nodeinfo["available"]["cpu"] * 0.02, 1)

    available_node_mem = nodeinfo["available"]["memory"] - mem_overhead_wiggle
    available_node_cpu = nodeinfo["available"]["cpu"] - cpu_overhead_wiggle

    # We always start from the top, and provide a choice that takes up the whole node.
    mem_limit = available_node_mem

    choices = {}
    for i in range(num_allocations):
        # CPU guarantee is proportional to the memory limit for this particular choice.
        # This makes sure we utilize all the memory on a node all the time.
        cpu_guarantee = (mem_limit / available_node_mem) * available_node_cpu

        # Memory is in bytes, let's convert it to GB or MB (with no digits after 0) to display
        if mem_limit < 1024 * 1024 * 1024:
            mem_display = f"{mem_limit / 1024 / 1024:.0f} MB"
        else:
            mem_display = f"{mem_limit / 1024 / 1024 / 1024:.0f} GB"

        if cpu_guarantee < 2:
            cpu_guarantee_display = f"~{cpu_guarantee:0.1f}"
        else:
            cpu_guarantee_display = f"~{cpu_guarantee:0.0f}"

        display_name = f"{mem_display} RAM, {cpu_guarantee_display} CPUs"
        if cpu_guarantee != available_node_cpu:
            description = f"Upto ~{available_node_cpu:.0f} CPUs when available"
        else:
            description = f"~{available_node_cpu:.0f} CPUs always available"

        choice = {
            "display_name": display_name,
            "description": description,
            "kubespawner_override": {
                # Guarantee and Limit are the same - this strategy has no oversubscription
                "mem_guarantee": int(mem_limit),
                "mem_limit": int(mem_limit),
                "cpu_guarantee": cpu_guarantee,
                # CPU limit is set to entire available CPU of the node, making sure no single
                # user can starve the node of critical kubelet / systemd resources.
                # Leaving it unset sets it to same as guarantee, which we do not want.
                "cpu_limit": available_node_cpu,
                # Explicitly set node_selector here, so the output can be easily combined
                # multiple times, with multiple instance types
                "node_selector": {"node.kubernetes.io/instance-type": instance_type},
            },
        }

        # Use the amount of RAM made available as a slug, to allow combining choices from
        # multiple instance types in the same profile. This does mean you can not have
        # the same RAM allocation from multiple node selectors. But that's a feature, not a bug.
        choice_key = f"mem_{mem_display.replace('.', '_').replace(' ', '_')}".lower()
        choices[choice_key] = choice

        # Halve the mem_limit for the next choice
        mem_limit = mem_limit / 2

    # Reverse the choices so the smallest one is first
    choices = dict(reversed(choices.items()))

    return choices


@resource_allocation_app.command()
def choices(
    instance_specification: List[str] = typer.Argument(
        ...,
        help="Instance type and number of choices to generate Resource Allocation options for. Specify as instance_type:count.",
    ),
    strategy: ResourceAllocationStrategies = typer.Option(
        ResourceAllocationStrategies.PROPORTIONAL_MEMORY_STRATEGY,
        help="Strategy to use for generating resource allocation choices choices",
    ),
):
    """
    Generate a custom number of resource allocation choices for a certain instance type,
    depending on a certain chosen strategy.
    """
    with open(HERE / "node-capacity-info.json") as f:
        nodeinfo = json.load(f)
    choices = {}
    for instance_spec in instance_specification:
        instance_type, num_allocations = instance_spec.split(":", 2)

        if instance_type not in nodeinfo:
            print(
                f"Capacity information about {instance_type} not available",
                file=sys.stderr,
            )
            print("TODO: Provide information on how to update it", file=sys.stderr)
            sys.exit(1)

        # Call appropriate function based on what strategy we want to use
        if strategy == ResourceAllocationStrategies.PROPORTIONAL_MEMORY_STRATEGY:
            choices.update(
                proportional_memory_strategy(
                    instance_type, nodeinfo[instance_type], int(num_allocations)
                )
            )
        else:
            raise ValueError(f"Strategy {strategy} is not currently supported")
    yaml.dump(choices, sys.stdout)
