import os
import subprocess
from pathlib import Path

import jinja2
import typer

from .cli_app import app

REPO_ROOT = Path(__file__).parent.parent


def aws(cluster_name, hub_type, cluster_region):
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
        "hub_type": hub_type,
        "cluster_region": cluster_region,
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


def gcp(cluster_name, cluster_region, cluster_zone, project_id, hub_type):
    """
    Generates the cluster_name.tfvars terraform file
    required to create a GCP cluster
    """

    with open(REPO_ROOT / f"terraform/gcp/projects/{hub_type}-template.tfvars") as f:
        tfvars_template = jinja2.Template(f.read())

    vars = {
        "cluster_name": cluster_name,
        "cluster_region": cluster_region,
        "cluster_zone": cluster_zone,
        "project_id": project_id,
    }

    with open(
        REPO_ROOT / "terraform/gcp/projects" / f"{cluster_name}.tfvars", "w"
    ) as f:
        f.write(tfvars_template.render(**vars))


@app.command()
def generate_aws_cluster(
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
    aws(cluster_name, hub_type, cluster_region)


@app.command()
def generate_gcp_cluster(
    cluster_name: str = typer.Option(..., prompt="Name of the cluster to deploy"),
    cluster_region: str = typer.Option(
        ..., prompt="The region where to deploy the cluster"
    ),
    cluster_zone: str = typer.Option(
        ..., prompt="The zone where to deploy the cluster, eg. us-west2-b"
    ),
    project_id: str = typer.Option(
        ..., prompt="The GCP Project ID to create resources in"
    ),
    hub_type: str = typer.Option(
        ..., prompt="Type of hub. Choose from `basehub` or `daskhub`"
    ),
):
    """
    Automatically generate the terraform config file required to setup a new cluster on GCP
    """
    gcp(cluster_name, cluster_region, cluster_zone, project_id, hub_type)
