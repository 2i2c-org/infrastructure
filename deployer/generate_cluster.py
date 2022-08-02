import subprocess
from pathlib import Path

import jinja2

REPO_ROOT = Path(__file__).parent.parent


def aws(cluster_name):
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

    subprocess.check_call(
        [
            "sops",
            "--in-place",
            "--encrypt",
            f"{REPO_ROOT}/eksctl/ssh-keys/{cluster_name}.key",
        ]
    )


def generate_cluster(cloud_provider, cluster_name):
    if cloud_provider == "aws":
        aws(cluster_name)
    else:
        raise ValueError(f"Cloud Provider {cloud_provider} not supported")
