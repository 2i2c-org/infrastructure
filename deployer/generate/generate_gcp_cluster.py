"""
Generates the ` terraform file required to create a GCP cluster
and the required `config` directory for hubs on a GCP cluster.

Generates the following files:
- terraform/gcp/projects/<cluster_name>.tfvars`
- `config/<cluster_name>/cluster.yaml`
- `config/<cluster_name>/support.values.yaml`
- `config/<cluster_name>/enc-support.secret.values.yaml`

"""
import jinja2
import typer

from ..cli_app import app
from ..utils import print_colour
from .common import (
    REPO_ROOT,
    generate_cluster_config_file,
    generate_config_directory,
    generate_support_files,
)


def generate_terraform_file(vars):
    """
    Generates the `terraform/gcp/projects/<cluster_name>.tfvars` terraform file
    required to create a GCP cluster
    """
    with open(
        REPO_ROOT / f'terraform/gcp/projects/{vars["hub_type"]}-template.tfvars'
    ) as f:
        tfvars_template = jinja2.Template(f.read())

    print_colour("Generating the terraform infrastructure file...", "yellow")
    tfvars_file_path = (
        REPO_ROOT / "terraform/gcp/projects" / f'{vars["cluster_name"]}.tfvars'
    )
    with open(tfvars_file_path, "w") as f:
        f.write(tfvars_template.render(**vars))
    print_colour(f"{tfvars_file_path} created")


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
    Automatically generates the initial files, required to setup a new cluster on GCP
    """
    # Automatically generate the terraform config file
    generate_terraform_file(cluster_name, cluster_region, project_id, hub_type)

    # These are the variables needed by the templates used to generate the cluster config file
    # and support files
    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
        "project_id": project_id,
        "hub_name": hub_name,
    }

    # Automatically generate the config directory
    cluster_config_directory = generate_config_directory(vars)

    # Create the cluster config directory and initial `cluster.yaml` file
    generate_cluster_config_file(cluster_config_directory, "gcp", vars)

    # Generate the support files
    generate_support_files(cluster_config_directory, vars)
