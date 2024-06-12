"""
Generate required files for an AWS cluster

Generates:
- an eksctl jsonnet file
- a .tfvars file
- An ssh-key (the private part is encrypted)
"""

import os
import subprocess

import jinja2
import typer
from typing_extensions import Annotated

from deployer.utils.file_acquisition import REPO_ROOT_PATH
from deployer.utils.rendering import print_colour

from .common import (
    check_before_continuing_with_generate_command,
    generate_config_directory,
    generate_support_files,
)
from .dedicated_cluster_app import dedicated_cluster_app


def get_infra_files_to_be_created(cluster_name):
    return [
        REPO_ROOT_PATH / "eksctl" / f"{cluster_name}.jsonnet",
        REPO_ROOT_PATH / "terraform/aws/projects" / f"{cluster_name}.tfvars",
        REPO_ROOT_PATH / "eksctl/ssh-keys/secret" / f"{cluster_name}.key",
        REPO_ROOT_PATH / "config/clusters" / cluster_name / "support.values.yaml",
        REPO_ROOT_PATH
        / "config/clusters"
        / cluster_name
        / "enc-support.secret.values.yaml",
        REPO_ROOT_PATH / "config/clusters" / cluster_name / "cluster.yaml",
    ]


def generate_infra_files(vars):
    cluster_name = vars["cluster_name"]
    with open(REPO_ROOT_PATH / "eksctl/template.jsonnet") as f:
        # jsonnet files have `}}` in there, which causes jinja2 to
        # freak out. So we use different delimiters.
        jsonnet_template = jinja2.Template(
            f.read(),
            trim_blocks=True,
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="<<",
            variable_end_string=">>",
        )

    print_colour("Generating the eksctl jsonnet file...", "yellow")
    jsonnet_file_path = REPO_ROOT_PATH / "eksctl" / f"{cluster_name}.jsonnet"
    with open(jsonnet_file_path, "w") as f:
        f.write(jsonnet_template.render(**vars))
    print_colour(f"{jsonnet_file_path} created")

    print_colour("Generating the terraform infrastructure file...", "yellow")
    with open(REPO_ROOT_PATH / "terraform/aws/projects/template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())
    tfvars_file_path = (
        REPO_ROOT_PATH / "terraform/aws/projects" / f"{cluster_name}.tfvars"
    )
    with open(tfvars_file_path, "w") as f:
        f.write(tfvars_template.render(**vars))
    print_colour(f"{tfvars_file_path} created")

    print_colour("Generate, encrypt and store the ssh private key...", "yellow")
    subprocess.check_call(
        [
            "ssh-keygen",
            "-f",
            f"{REPO_ROOT_PATH}/eksctl/ssh-keys/{cluster_name}.key",
            "-q",
            "-N",
            "",
        ]
    )

    # Move the generated ssh private key file under secret/
    os.rename(
        f"{REPO_ROOT_PATH}/eksctl/ssh-keys/{cluster_name}.key",
        f"{REPO_ROOT_PATH}/eksctl/ssh-keys/secret/{cluster_name}.key",
    )

    ssh_key_file = REPO_ROOT_PATH / "eksctl/ssh-keys/secret" / f"{cluster_name}.key"
    # Encrypt the private key
    subprocess.check_call(
        [
            "sops",
            "--in-place",
            "--encrypt",
            ssh_key_file,
        ]
    )
    print_colour(f"{ssh_key_file} created")


@dedicated_cluster_app.command()
def aws(
    cluster_name: str = typer.Option(..., prompt="Name of the cluster to deploy"),
    cluster_region: str = typer.Option(
        ..., prompt="The region where to deploy the cluster"
    ),
    hub_type: Annotated[
        str,
        typer.Option(
            prompt="Please type in the hub type: basehub/daskhub.\n-> If this cluster will host daskhubs, please type `daskhub`.\n-> If you don't know this info, or this is not the case, just hit ENTER"
        ),
    ] = "basehub",
    force: bool = typer.Option(
        False,
        "--force",
        help="Whether or not to force the override of the files that already exist",
    ),
):
    """
    Automatically generate the files required to setup a new cluster on AWS if they don't exist.
    Use --force to force existing configuration files to be overwritten by this command.
    """
    # These are the variables needed by the templates used to generate the cluster config file
    # and support files

    vars = {
        # Also store the provider, as it's useful for some jinja templates
        # to differentiate between them when rendering the configuration
        "provider": "aws",
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
    }

    if not check_before_continuing_with_generate_command(
        get_infra_files_to_be_created, cluster_name, force
    ):
        raise typer.Abort()

    # If we are here, then either no existing infrastructure files for this cluster have been found
    # or the `--force` flag was provided and we can override existing files.
    generate_infra_files(vars)
    # Automatically generate the config directory
    cluster_config_directory = generate_config_directory(vars)
    # Generate the support files
    generate_support_files(cluster_config_directory, vars)
