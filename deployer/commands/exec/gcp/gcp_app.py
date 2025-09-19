"""
Creates a new typer application, which is then
nested as a sub-command named "gcp"
under the `exec` sub-command of the deployer.

Helper methods for commandline access to AWS.
"""

import json
import subprocess

import typer

from deployer.cli_app import exec_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.rendering import print_colour

gcp = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(
    gcp,
    name="gcp",
    help="Helper methods for commandline access to GCP.",
)


@gcp.command()
def home_disk(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="The name of the (new) hub"),
    disk_size: int = typer.Option(10, help="Size of the new disk in GB"),
    disk_type: str = typer.Option("pd-balanced", help="Type of disk to create"),
):
    """
    Create a home-directory disk on GCP
    """

    cluster = Cluster.from_name(cluster_name)
    provider = cluster.spec["provider"]
    if provider != "gcp":
        print_colour(
            f"Cluster {cluster_name} is not a GCP cluster",
            "red",
        )
        exit(1)

    for hub in cluster.hubs:
        if hub.spec["name"] == hub_name:
            print_colour(
                f"Hub {hub_name} already exists",
                "red",
            )
            exit(1)

    project = cluster.spec["gcp"]["project"]
    zone = cluster.spec["gcp"]["zone"]

    # Create the disk
    output = subprocess.check_output(
        [
            "gcloud",
            "compute",
            "disks",
            "create",
            f"hub-nfs-homedirs-{hub_name}",
            f"--size={disk_size}",
            f"--type=https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/diskTypes/{disk_type}",
            f"--zone={zone}",
            f"--project={project}",
            "--format=json",
        ],
        text=True,
        stderr=subprocess.PIPE,
    )
    disks = json.loads(output)

    if len(disks) != 1:
        print_colour(
            f"Expected 1 new disk, encountered {len(disks)}",
            "red",
        )
        exit(1)

    disk = disks[0]
    disk_uri = disk["selfLink"]
    disk_size_gb = disk["sizeGb"]
    assert int(disk_size_gb) == disk_size

    # Make sure we have proper URI
    prefix = "https://www.googleapis.com/compute/v1/"
    assert disk_uri.startswith(prefix)
    volume_id = disk_uri.removeprefix(prefix)

    print(
        f"""
# Terraform config:
"{hub_name}" = {{
    size = {disk_size}
    name_suffix = "{hub_name}"
}}

# NFS config:
# https://infrastructure.2i2c.org/howto/features/storage-quota/#enabling-jupyterhub-home-nfs
volumeId: {volume_id}
"""
    )
