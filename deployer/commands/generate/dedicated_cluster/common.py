import os
import secrets
import string
import subprocess

import jinja2

from deployer.utils.file_acquisition import REPO_ROOT_PATH
from deployer.utils.rendering import print_colour


def infra_files_already_exist(get_infra_files_func, cluster_name):
    infra_files = get_infra_files_func(cluster_name)
    if any(os.path.exists(path) for path in infra_files):
        return True

    return False


def force_overwrite(get_infra_files_func, cluster_name, force):
    if infra_files_already_exist(get_infra_files_func, cluster_name):
        if not force:
            print_colour(
                f"Found existing infrastructure files for cluster {cluster_name}. Use --force if you want to allow this script to overwrite them.",
                "red",
            )
            return False
        else:
            print_colour(
                f"Attention! Found existing infrastructure files for {cluster_name}. They will be overwritten by the --force flag!",
                "red",
            )
    return True


def generate_cluster_config_file(cluster_config_directory, provider, vars):
    """
    Generates the `config/<cluster_name>/cluster.yaml` config
    """
    print_colour("Generating the cluster.yaml config file...", "yellow")
    with open(
        REPO_ROOT_PATH / f"config/clusters/templates/{provider}/cluster.yaml"
    ) as f:
        cluster_yaml_template = jinja2.Template(f.read())
    cluster_yaml_file = cluster_config_directory / "cluster.yaml"
    with open(cluster_yaml_file, "w") as f:
        f.write(cluster_yaml_template.render(**vars))
        print_colour(f"{cluster_yaml_file} created")


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
    with open(
        REPO_ROOT_PATH / "config/clusters/templates/common/support.values.yaml"
    ) as f:
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
        REPO_ROOT_PATH / "config/clusters/templates/common/support.secret.values.yaml"
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


def generate_config_directory(vars):
    """
    Generates the required `config` directory for hubs on a cluster if it doesn't exit
    and returns its name.
    """
    cluster_config_directory = REPO_ROOT_PATH / "config/clusters" / vars["cluster_name"]

    print_colour(
        f"Checking if cluster config directory {cluster_config_directory} exists...",
        "yellow",
    )
    if os.path.exists(cluster_config_directory):
        print_colour(f"{cluster_config_directory} already exists.")
        return cluster_config_directory

    # Create the cluster config directory and initial `cluster.yaml` file
    os.makedirs(cluster_config_directory)
    print_colour(f"{cluster_config_directory} created")

    return cluster_config_directory
