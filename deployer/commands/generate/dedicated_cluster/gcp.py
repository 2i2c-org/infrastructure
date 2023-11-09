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
from typing_extensions import Annotated

from deployer.utils.file_acquisition import REPO_ROOT_PATH
from deployer.utils.rendering import print_colour

from .common import (
    force_overwrite,
    generate_cluster_config_file,
    generate_config_directory,
    generate_support_files,
)
from .dedicated_cluster_app import dedicated_cluster_app


def get_infra_files_to_be_created(cluster_name):
    return [
        REPO_ROOT_PATH / "terraform/gcp/projects" / f"{cluster_name}.tfvars",
        REPO_ROOT_PATH / "config/clusters" / cluster_name / "support.values.yaml",
        REPO_ROOT_PATH
        / "config/clusters"
        / cluster_name
        / "enc-support.secret.values.yaml",
        REPO_ROOT_PATH / "config/clusters" / cluster_name / "cluster.yaml",
    ]


def generate_terraform_file(vars):
    """
    Generates the `terraform/gcp/projects/<cluster_name>.tfvars` terraform file
    required to create a GCP cluster
    """
    with open(
        REPO_ROOT_PATH / f'terraform/gcp/projects/{vars["hub_type"]}-template.tfvars'
    ) as f:
        tfvars_template = jinja2.Template(f.read())

    print_colour("Generating the terraform infrastructure file...", "yellow")
    tfvars_file_path = (
        REPO_ROOT_PATH / "terraform/gcp/projects" / f'{vars["cluster_name"]}.tfvars'
    )
    with open(tfvars_file_path, "w") as f:
        f.write(tfvars_template.render(**vars))
    print_colour(f"{tfvars_file_path} created")


@dedicated_cluster_app.command()
def gcp(
    cluster_name: Annotated[
        str, typer.Option(prompt="Please type the name of the new cluster")
    ],
    project_id: Annotated[
        str, typer.Option(prompt="Please insert the Project ID of the GCP project")
    ],
    hub_name: Annotated[
        str,
        typer.Option(
            prompt="Please insert the name of first hub to add to the cluster"
        ),
    ],
    cluster_region: Annotated[
        str, typer.Option(prompt="Please insert the name of the cluster region")
    ] = "us-central1",
    hub_type: Annotated[
        str, typer.Option(prompt="Please insert the hub type of the first hub")
    ] = "basehub",
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Whether or not to force the override of the files that already exist",
        ),
    ] = False,
):
    """
    Automatically generates the initial files, required to setup a new cluster on GCP if they don't exist.
    Use --force to force existing configuration files to be overwritten by this command.
    """
    # These are the variables needed by the templates used to generate the cluster config file
    # and support files
    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
        "project_id": project_id,
        "hub_name": hub_name,
    }

    if not force_overwrite(get_infra_files_to_be_created, cluster_name, force):
        raise typer.Abort()

    # If we are here, then either no existing infrastructure files for this cluster have been found
    # or the `--force` flag was provided and we can override existing files.

    # Automatically generate the terraform config file
    generate_terraform_file(vars)

    # Automatically generate the config directory
    cluster_config_directory = generate_config_directory(vars)

    # Create the cluster config directory and initial `cluster.yaml` file
    generate_cluster_config_file(cluster_config_directory, "gcp", vars)

    # Generate the support files
    generate_support_files(cluster_config_directory, vars)
