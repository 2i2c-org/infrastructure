import os
import secrets
import string
import subprocess
from pathlib import Path

import jinja2
import typer

from .cli_app import app
from .utils import print_colour

REPO_ROOT = Path(__file__).parent.parent


def gcp_infrastructure_files(cluster_name, cluster_region, project_id, hub_type):
    """
    Generates the cluster_name.tfvars terraform file
    required to create a GCP cluster
    """

    with open(REPO_ROOT / f"terraform/gcp/projects/{hub_type}-template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())

    vars = {
        "cluster_name": cluster_name,
        "cluster_region": cluster_region,
        "project_id": project_id,
    }

    with open(
        REPO_ROOT / "terraform/gcp/projects" / f"{cluster_name}.tfvars", "w"
    ) as f:
        f.write(tfvars_template.render(**vars))


def gcp_config_files(cluster_name, cluster_region, project_id, hub_type, hub_name):
    """
    Generates the required `config` directory and files for hubs on a GCP cluster

    Generates the following files, in the <cluster_name> directory:
    - cluster.yaml file
    - support.values.yaml file
    - enc-support.secret.values.yaml file
    """

    cluster_config_directory = REPO_ROOT / "config/clusters" / cluster_name

    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
        "project_id": project_id,
        "hub_name": hub_name
    }

    print_colour("Checking if cluster config directory {cluster_config_directory} exists...", "yellow")
    if not os.path.exists(cluster_config_directory):
        os.makedirs(cluster_config_directory)
        print_colour(f"Done!")

        with open(REPO_ROOT / "config/clusters/templates/gcp/cluster.yaml") as f:
            cluster_yaml_template = jinja2.Template(f.read())
        with open(
            cluster_config_directory / "cluster.yaml", "w"
        ) as f:
            f.write(cluster_yaml_template.render(**vars))
    else:
        print_colour(f"Cluster config directory already exists -> {cluster_config_directory}.", "yellow")
        return

    print_colour("Generating the support values file...", "yellow")
    with open(REPO_ROOT / "config/clusters/templates/gcp/support.values.yaml") as f:
        support_values_yaml_template = jinja2.Template(f.read())
    with open(
        cluster_config_directory / "support.values.yaml", "w"
    ) as f:
        f.write(support_values_yaml_template.render(**vars))
    print_colour("Done!")

    print_colour("Generating the prometheus credentials encrypted file...", "yellow")
    alphabet = string.ascii_letters + string.digits
    credentials = {
        "username": ''.join(secrets.choice(alphabet) for i in range(64)),
        "password": ''.join(secrets.choice(alphabet) for i in range(64))
    }
    with open(REPO_ROOT / "config/clusters/templates/gcp/support.secret.values.yaml") as f:
        support_secret_values_yaml_template = jinja2.Template(f.read())
    with open(
        cluster_config_directory / "enc-support.secret.values.yaml", "w"
    ) as f:
        f.write(support_secret_values_yaml_template.render(**credentials))

    # Encrypt the private key
    subprocess.check_call(
        [
            "sops",
            "--in-place",
            "--encrypt",
            cluster_config_directory / "enc-support.secret.values.yaml"
        ]
    )

@app.command()
def generate_gcp_cluster(
    cluster_name: str = typer.Option(..., prompt="Name of the cluster where the hub will be deployed"),
    cluster_region: str = typer.Option(
        ..., prompt="The region the cluster is or will be in"
    ),
    project_id: str = typer.Option(
        ..., prompt="Project ID of the GCP project that contains this cluster"
    ),
    hub_type: str = typer.Option(
        ..., prompt="Type of hub. Choose from `basehub` or `daskhub`"
    ),
    hub_name: str = typer.Option(
        ..., prompt="Name of the hub"
    ),
):
    """
    """
    # Automatically generate the terraform config file required to setup a new cluster on GCP
    gcp_infrastructure_files(cluster_name, cluster_region, project_id, hub_type)

    # Automatically generate the config directory required to setup a new cluster on GCP
    gcp_config_files(cluster_name, cluster_region, project_id, hub_type, hub_name)
