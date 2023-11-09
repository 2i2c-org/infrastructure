import os
import secrets
import string
import subprocess

import jinja2
from git import Repo

from deployer.utils.file_acquisition import REPO_ROOT_PATH
from deployer.utils.rendering import print_colour


def check_force_overwrite(cluster_name, force):
    """
    Check if the force flag is present and print relevant messages to stdout.
    If  the --force flag was False, return False, otherwise, return True.
    """
    if not force:
        print_colour(
            f"Found existing infrastructure files for cluster {cluster_name}. Use --force if you want to allow this script to overwrite them.",
            "red",
        )
        return False

    print_colour(
        f"Attention! Found existing infrastructure files for {cluster_name}. They will be overwritten by the --force flag!",
        "red",
    )

    return True


def check_git_status_clean(infra_files):
    """
    Check if running `git status` doesn't return any file that the generate command should create/update.
    If any of the files in `infra_files` (the files that the script will generate) are in the `git status` output,
    then return False, otherwise True.
    """
    repo = Repo(REPO_ROOT_PATH)
    status = repo.git.status("--porcelain")
    list_of_modified_files = status.split("\n")

    for file in list_of_modified_files:
        file = file.lstrip("?? ") if file.startswith("?? ") else file.lstrip(" M ")
        full_filepath = REPO_ROOT_PATH / file
        if full_filepath in infra_files:
            print_colour(
                f"{full_filepath} was not comitted. Commit or restore the file in order to proceed with the generation.",
                "yellow",
            )
            return False
    return True


def check_before_continuing_with_generate_command(
    get_infra_files_func, cluster_name, force
):
    """
    This function does a sanity check of the current state of infrastructure files of the desired cluster.
    These checks will then be used to decide if the functions generating the files will be ran.

    The checks are:
    1. if any of the files that will be generated are found in the `git status` output, then return False
    2. else, if none of the infrastructure files that the script will generate exist, then return True
    3. else, if there are infrastructure files that already exist and the --force flag was not used, then return False
    $. Otherwise, return True
    """
    infra_files = get_infra_files_func(cluster_name)
    if not check_git_status_clean(infra_files):
        return False

    if not (any(os.path.exists(path) for path in infra_files)):
        return True

    if not check_force_overwrite(cluster_name, force):
        return False

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
