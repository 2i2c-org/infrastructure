import os
import secrets
import string
import subprocess
from pathlib import Path

import jinja2
import typer

from ..cli_app import app
from ..utils import print_colour

REPO_ROOT = Path(__file__).parent.parent.parent


def generate_terraform_file(cluster_name, cluster_region, project_id, hub_type):
    """
    Generates the `terraform/gcp/projects/<cluster_name>.tfvars` terraform file
    required to create a GCP cluster
    """
    with open(REPO_ROOT / f"terraform/gcp/projects/{hub_type}-template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())

    vars = {
        "cluster_name": cluster_name,
        "cluster_region": cluster_region,
        "project_id": project_id,
    }

    print_colour("Generating the terraform infrastructure file...", "yellow")
    with open(
        REPO_ROOT / "terraform/gcp/projects" / f"{cluster_name}.tfvars", "w"
    ) as f:
        f.write(tfvars_template.render(**vars))
    print_colour(f"{REPO_ROOT}/terraform/gcp/projects/{cluster_name}.tfvars created")


def generate_cluster_config_file(cluster_config_directory, vars):
    """
    Generates the `config/<cluster_name>/cluster.yaml` config
    """
    with open(REPO_ROOT / "config/clusters/templates/gcp/cluster.yaml") as f:
        cluster_yaml_template = jinja2.Template(f.read())
    with open(cluster_config_directory / "cluster.yaml", "w") as f:
        f.write(cluster_yaml_template.render(**vars))


def generate_support_files(cluster_config_directory, vars):
    """
    Generates files related to support components.

    They are required to deploy the support chart for the cluster
    and to configure the Prometheus instance.

    Generates:
        - `config/<cluster_name>/support.values.yaml`
        - `config/<cluster_name>/enc-support.secret.values.yaml`
    """
    # Generate the suppport values file `support.values.yaml`
    print_colour("Generating the support values file...", "yellow")
    with open(REPO_ROOT / "config/clusters/templates/gcp/support.values.yaml") as f:
        support_values_yaml_template = jinja2.Template(f.read())

    with open(cluster_config_directory / "support.values.yaml", "w") as f:
        f.write(support_values_yaml_template.render(**vars))
    print_colour(f"{cluster_config_directory}/support.values.yaml created")

    # Generate and encrypt prometheus credentials into `enc-support.secret.values.yaml`
    print_colour("Generating the prometheus credentials encrypted file...", "yellow")
    alphabet = string.ascii_letters + string.digits
    credentials = {
        "username": "".join(secrets.choice(alphabet) for i in range(64)),
        "password": "".join(secrets.choice(alphabet) for i in range(64)),
    }
    with open(
        REPO_ROOT / "config/clusters/templates/gcp/support.secret.values.yaml"
    ) as f:
        support_secret_values_yaml_template = jinja2.Template(f.read())
    with open(cluster_config_directory / "enc-support.secret.values.yaml", "w") as f:
        f.write(support_secret_values_yaml_template.render(**credentials))

    # Encrypt the private key
    subprocess.check_call(
        [
            "sops",
            "--in-place",
            "--encrypt",
            cluster_config_directory / "enc-support.secret.values.yaml",
        ]
    )
    print_colour(
        f"{cluster_config_directory}/enc-support.values.yaml created and encrypted"
    )


def generate_config_directory(
    cluster_name, cluster_region, project_id, hub_type, hub_name
):
    """
    Generates the required `config` directory for hubs on a GCP cluster

    Generates the following files:
    - `config/<cluster_name>/cluster.yaml`
    - `config/<cluster_name>/support.values.yaml`
    - `config/<cluster_name>/enc-support.secret.values.yaml`
    """

    cluster_config_directory = REPO_ROOT / "config/clusters" / cluster_name

    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
        "project_id": project_id,
        "hub_name": hub_name,
    }

    print_colour(
        "Checking if cluster config directory {cluster_config_directory} exists...",
        "yellow",
    )
    if os.path.exists(cluster_config_directory):
        print_colour(f"{cluster_config_directory} already exists.")
        return

    # Create the cluster config directory and initial `cluster.yaml` file
    os.makedirs(cluster_config_directory)
    print_colour(f"{cluster_config_directory} created")
    generate_cluster_config_file(cluster_config_directory, vars)

    # Generate the support files
    generate_support_files(cluster_config_directory, vars)


@app.command()
def generate_gcp_cluster(
    cluster_name: str = typer.Option(..., prompt="Name of the cluster"),
    cluster_region: str = typer.Option(..., prompt="Cluster region"),
    project_id: str = typer.Option(..., prompt="Project ID of the GCP project"),
    hub_type: str = typer.Option(
        ..., prompt="Type of hub. Choose from `basehub` or `daskhub`"
    ),
    hub_name: str = typer.Option(..., prompt="Name of the first hub"),
):
    """
    Automatically generates the default intitial files required to setup a new cluster on GCP
    """
    # Automatically generate the terraform config file
    generate_terraform_file(cluster_name, cluster_region, project_id, hub_type)

    # Automatically generate the config directory
    generate_config_directory(
        cluster_name, cluster_region, project_id, hub_type, hub_name
    )
