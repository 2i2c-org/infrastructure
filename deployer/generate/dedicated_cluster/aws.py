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

from ...utils import print_colour
from .app import dedicated_cluster_app
from .common import REPO_ROOT, generate_config_directory, generate_support_files


def generate_infra_files(vars):
    cluster_name = vars["cluster_name"]
    with open(REPO_ROOT / "eksctl/template.jsonnet") as f:
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
    jsonnet_file_path = REPO_ROOT / "eksctl" / f"{cluster_name}.jsonnet"
    with open(jsonnet_file_path, "w") as f:
        f.write(jsonnet_template.render(**vars))
    print_colour(f"{jsonnet_file_path} created")

    print_colour("Generating the terraform infrastructure file...", "yellow")
    with open(REPO_ROOT / "terraform/aws/projects/template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())

    tfvars_file_path = REPO_ROOT / "terraform/aws/projects" / f"{cluster_name}.tfvars"
    with open(tfvars_file_path, "w") as f:
        f.write(tfvars_template.render(**vars))
    print_colour(f"{tfvars_file_path} created")

    subprocess.check_call(
        [
            "ssh-keygen",
            "-f",
            f"{REPO_ROOT}/eksctl/ssh-keys/{cluster_name}.key",
            "-q",
            "-N",
            "",
        ]
    )

    # Move the generated ssh private key file under secret/
    os.rename(
        f"{REPO_ROOT}/eksctl/ssh-keys/{cluster_name}.key",
        f"{REPO_ROOT}/eksctl/ssh-keys/secret/{cluster_name}.key",
    )

    # Encrypt the private key
    subprocess.check_call(
        [
            "sops",
            "--in-place",
            "--encrypt",
            f"{REPO_ROOT}/eksctl/ssh-keys/secret/{cluster_name}.key",
        ]
    )


@dedicated_cluster_app.command()
def aws(
    cluster_name: str = typer.Option(..., prompt="Name of the cluster to deploy"),
    hub_type: str = typer.Option(
        ..., prompt="Type of hub. Choose from `basehub` or `daskhub`"
    ),
    cluster_region: str = typer.Option(
        ..., prompt="The region where to deploy the cluster"
    ),
):
    """
    Automatically generate the files required to setup a new cluster on AWS
    """

    # These are the variables needed by the templates used to generate the cluster config file
    # and support files
    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type,
        "cluster_region": cluster_region,
    }

    generate_infra_files(vars)

    # Automatically generate the config directory
    cluster_config_directory = generate_config_directory(vars)

    # Generate the support files
    generate_support_files(cluster_config_directory, vars)
