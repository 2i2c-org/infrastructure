import os
import subprocess
from pathlib import Path

import jinja2
import typer

from .cli_app import app

REPO_ROOT = Path(__file__).parent.parent


def aws(cluster_name, hub_type):
    """
    Generate required files for an AWS cluster

    Generates:
    - an eksctl jsonnet file
    - a .tfvars file
    - An ssh-key (the private part is encrypted)
    """
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

    with open(REPO_ROOT / "terraform/aws/projects/template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())

    vars = {
        "cluster_name": cluster_name,
        "hub_type": hub_type
    }

    with open(REPO_ROOT / "eksctl" / f"{cluster_name}.jsonnet", "w") as f:
        f.write(jsonnet_template.render(**vars))

    with open(
        REPO_ROOT / "terraform/aws/projects" / f"{cluster_name}.tfvars", "w"
    ) as f:
        f.write(tfvars_template.render(**vars))

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

@app.command()
def generate_cluster(
    cloud_provider: str=typer.Option(..., prompt="Name of the cloud provider the cluster will be deployed to"),
    cluster_name: str=typer.Option(..., prompt="Name of the cluster to deploy"),
    hub_type: str=typer.Option(..., prompt="Type of hub: basehub/daskhub")
):
    """
    Automatically generate the files required to setup a new cluster on a specific cloud provider
    """
    if cloud_provider == "aws":
        aws(cluster_name, hub_type)
    else:
        raise ValueError(f"Cloud Provider {cloud_provider} not supported")
