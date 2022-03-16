"""
Functions related to deciding which clusters and/or hubs need their *hub helm chart or
support helm chart upgrading depending on an input list of filenames that have been
added or modified in a GitHub Pull Request.
"""
import fnmatch
import os
from pathlib import Path
from ruamel.yaml import YAML
from rich.console import Console
from rich.table import Table

yaml = YAML(typ="safe", pure=True)

# Determine if we are running a test or not. We set this env var to "test" in the
# pyproject.toml file so it is set when the package is tested using pytest.
test_env = os.getenv("RUN_ENV", False)


def discover_modified_common_files(modified_paths: list):
    """There are certain common files which, if modified, we should upgrade all hubs
    and/or all clusters appropriately. These common files include the helm charts we
    deploy, as well as the GitHub Actions and deployer package we use to deploy them.

    Args:
        modified_paths (list[str]): The list of files that have been added or modified
            in a given GitHub Pull Request.

    Returns:
        upgrade_support_on_all_clusters (bool): Whether or not all clusters should be
            upgraded since the support chart has changed
        upgrade_all_hubs_on_all_clusters (bool): Whether or not all hubs on all clusters
            should be upgraded since a core piece of infrastructure has changed
    """
    # If any of the following filepaths have changed, we should update all hubs on all clusters
    common_filepaths = [
        # Filepaths related to the deployer infrastructure
        "deployer/*",
        "requirements.txt",
        # Filepaths related to GitHub Actions infrastructure
        ".github/workflows/deploy-hubs.yaml",
        ".github/actions/deploy/*",
        # Filepaths related to helm chart infrastructure
        "helm-charts/basehub/*",
        "helm-charts/daskhub/*",
    ]
    # If this filepath has changes, we should update the support chart on all clusters
    support_chart_filepath = "helm-charts/support/*"

    # Discover if the support chart has been modified
    upgrade_support_on_all_clusters = bool(
        fnmatch.filter(modified_paths, support_chart_filepath)
    )

    # Discover if any common config has been modified
    upgrade_all_hubs_on_all_clusters = False
    for common_filepath_pattern in common_filepaths:
        upgrade_all_hubs_on_all_clusters = bool(
            fnmatch.filter(modified_paths, common_filepath_pattern)
        )
        if upgrade_all_hubs_on_all_clusters:
            break

    return upgrade_support_on_all_clusters, upgrade_all_hubs_on_all_clusters


def get_unique_cluster_filepaths(added_or_modified_files: list):
    """For a list of added and modified files, get the list of unique filepaths to
    cluster folders containing added/modified files

    Note: "cluster folders" are those that contain a cluster.yaml file.

    Args:
        added_or_modified_files (list[str]): A list of files that have been added or
            modified in a GitHub Pull Request

    Returns:
        list[path obj]: A list of unique filepaths to cluster folders
    """
    # Get absolute paths
    if test_env == "test":
        # We are running a test via pytest. We only want to focus on the cluster
        # folders nested under the `tests/` folder.
        filepaths = [
            Path(filepath).parent
            for filepath in added_or_modified_files
            if "tests/" in filepath
        ]
    else:
        # We are NOT running a test via pytest. We want to explicitly ignore the
        # cluster folders nested under the `tests/` folder.
        filepaths = [
            Path(filepath).parent
            for filepath in added_or_modified_files
            if "tests/" not in filepath
        ]

    # Get unique absolute paths
    filepaths = list(set(filepaths))

    # Check these filepaths are cluster folders by the existence of a cluster.yaml file
    for filepath in filepaths:
        if not filepath.joinpath("cluster.yaml").is_file():
            filepaths.remove(filepath)

    return filepaths


def generate_hub_matrix_jobs(
    cluster_filepaths,
    added_or_modified_files,
    upgrade_all_hubs_on_all_clusters=False,
):
    """Generate a list of dictionaries describing which hubs on which clusters need
    to undergo a helm upgrade based on whether their associated helm chart values
    files have been modified. To be parsed to GitHub Actions in order to generate
    parallel jobs in a matrix.

    Note: "cluster folders" are those that contain a cluster.yaml file.

    Args:
        cluster_filepaths (list[path obj]): List of absolute paths to cluster folders
        added_or_modified_files (set[str]): A set of all added or modified files
            provided in a GitHub Pull Requests
        upgrade_all_hubs_on_all_clusters (bool, optional): If True, generates jobs to
            upgrade all hubs on all clusters. This is triggered when common config has
            been modified, such as basehub or daskhub helm charts. Defaults to False.

    Returns:
        list[dict]: A list of dictionaries. Each dictionary contains: the name of a
            cluster, the cloud provider that cluster runs on, and the name of a hub
            deployed to that cluster.
    """
    # Empty list to store the matrix job definitions in
    matrix_jobs = []

    # This flag will allow us to establish when a cluster.yaml file has been updated
    # and all hubs on that cluster should be upgraded, without also upgrading all hubs
    # on all other clusters
    upgrade_all_hubs_on_this_cluster = False

    if upgrade_all_hubs_on_all_clusters:
        print(
            "Common config has been updated. Generating jobs to upgrade all hubs on ALL clusters."
        )

        # Overwrite cluster_filepaths to contain paths to all clusters
        if test_env == "test":
            # We are running a test via pytest. We only want to focus on the cluster
            # folders nested under the `tests/` folder.
            cluster_filepaths = [
                filepath.parent
                for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
                if "tests/" in str(filepath)
            ]
        else:
            # We are NOT running a test via pytest. We want to explicitly ignore the
            # cluster folders nested under the `tests/` folder.
            cluster_filepaths = [
                filepath.parent
                for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
                if "tests/" not in str(filepath)
            ]

    for cluster_filepath in cluster_filepaths:
        # Read in the cluster.yaml file
        with open(cluster_filepath.joinpath("cluster.yaml")) as f:
            cluster_config = yaml.load(f)

        if not upgrade_all_hubs_on_all_clusters:
            # Check if this cluster file has been modified. If so, set
            # upgrade_all_hubs_on_this_cluster to True
            intersection = added_or_modified_files.intersection(
                [str(cluster_filepath.joinpath("cluster.yaml"))]
            )
            if len(intersection) > 0:
                print(
                    f"This cluster.yaml file has been modified. Generating jobs to upgrade all hubs on THIS cluster: {cluster_config.get('name', {})}"
                )
                upgrade_all_hubs_on_this_cluster = True

        # Generate template dictionary for all jobs associated with this cluster
        cluster_info = {
            "cluster_name": cluster_config.get("name", {}),
            "provider": cluster_config.get("provider", {}),
        }

        # Loop over each hub on this cluster
        for hub in cluster_config.get("hubs", {}):
            if upgrade_all_hubs_on_all_clusters or upgrade_all_hubs_on_this_cluster:
                # We know we're upgrading all hubs, so just add the hub name to the list
                # of matrix jobs and move on
                matrix_job = cluster_info.copy()
                matrix_job["hub_name"] = hub["name"]
                matrix_jobs.append(matrix_job)

            else:
                # Read in this hub's helm chart values files from the cluster.yaml file
                helm_chart_values_files = [
                    str(cluster_filepath.joinpath(values_file))
                    for values_file in hub.get("helm_chart_values_files", {})
                ]
                # Establish if any of this hub's helm chart values files have been
                # modified
                intersection = list(
                    added_or_modified_files.intersection(helm_chart_values_files)
                )

                if len(intersection) > 0:
                    # If at least one of the helm chart values files associated with
                    # this hub has been modified, add it to list of matrix jobs to be
                    # upgraded
                    matrix_job = cluster_info.copy()
                    matrix_job["hub_name"] = hub["name"]
                    matrix_jobs.append(matrix_job)

        # Reset upgrade_all_hubs_on_this_cluster for the next iteration
        upgrade_all_hubs_on_this_cluster = False

    return matrix_jobs


def generate_support_matrix_jobs(
    cluster_filepaths, added_or_modified_files, upgrade_support_on_all_clusters=False
):
    """Generate a list of dictionaries describing which clusters need to undergo a helm
    upgrade of their support chart based on whether their cluster.yaml file or
    associated support chart values files have been modified. To be parsed to GitHub
    Actions in order to generate parallel jobs in a matrix.

    Note: "cluster folders" are those that contain a cluster.yaml file.

    Args:
        cluster_filepaths (list[path obj]): List of absolute paths to cluster folders
            that contain added or modified files from the input of a GitHub Pull
            Request
        added_or_modified_files (set): A set of all added or modified files from the
            input of a GitHub Pull Request
        upgrade_support_on_all_clusters (bool, optional): If True, generates jobs to
            update the support chart on all clusters. This is triggered when common
            config has been modified in the support helm chart. Defaults to False.

    Returns:
        list[dict]: A list of dictionaries. Each dictionary contains: the name of a
            cluster and the cloud provider that cluster runs on.
    """
    # Empty list to store the matrix definitions in
    matrix_jobs = []

    if upgrade_support_on_all_clusters:
        print(
            "Common config has been updated. Generating jobs to upgrade support chart on ALL clusters."
        )

        # Overwrite cluster_filepaths to contain paths to all clusters
        if test_env == "test":
            # We are running a test via pytest. We only want to focus on the cluster
            # folders nested under the `tests/` folder.
            cluster_filepaths = [
                filepath.parent
                for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
                if "tests/" in str(filepath)
            ]
        else:
            # We are NOT running a test via pytest. We want to explicitly ignore the
            # cluster folders nested under the `tests/` folder.
            cluster_filepaths = [
                filepath.parent
                for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
                if "tests/" not in str(filepath)
            ]

    for cluster_filepath in cluster_filepaths:
        # Read in the cluster.yaml file
        with open(cluster_filepath.joinpath("cluster.yaml")) as f:
            cluster_config = yaml.load(f)

        # Generate a dictionary-style job entry for this cluster
        cluster_info = {
            "cluster_name": cluster_config.get("name", {}),
            "provider": cluster_config.get("provider", {}),
        }

        # Double-check that support is defined for this cluster.
        support_config = cluster_config.get("support", {})
        if support_config:
            if upgrade_support_on_all_clusters:
                # We know we're upgrading all hubs, so just add the hub name to the list
                # of matrix jobs and move on
                matrix_jobs.append(cluster_info)
            else:
                # Has the cluster.yaml file for this cluster folder been modified?
                cluster_yaml_intersection = added_or_modified_files.intersection(
                    [str(cluster_filepath.joinpath("cluster.yaml"))]
                )

                # Have the related support values files for this cluster been modified?
                support_values_files = [
                    str(cluster_filepath.joinpath(values_file))
                    for values_file in support_config.get("helm_chart_values_files", {})
                ]
                support_values_intersection = added_or_modified_files.intersection(
                    support_values_files
                )

                # If either of the intersections have a length greater than zero, append
                # the job definition to the list of matrix jobs
                if (len(cluster_yaml_intersection) > 0) or (
                    len(support_values_intersection) > 0
                ):
                    matrix_jobs.append(cluster_info)
        else:
            print(f"No support defined for cluster: {cluster_config.get('name', {})}")

    return matrix_jobs


def update_github_env(hub_matrix_jobs, support_matrix_jobs):
    """Update the GITHUB_ENV environment with two new variables describing the matrix
    jobs that need to be run in order to update the support charts and hubs that have
    been modified.
    Args:
        hub_matrix_jobs (list[dict]): A list of dictionaries which describe the set of
            matrix jobs required to update only the hubs on clusters whose config has
            been modified.
        support_matrix_jobs (list[dict]):  A list of dictionaries which describe the
            set of matrix jobs required to update only the support chart on clusters
            whose config has been modified.
    """
    # In GitHub Actions, the environment a workflow/job/step executes in can be
    # influenced by the contents of the `GITHUB_ENV` file.
    #
    # For more information, see:
    # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-environment-variable
    with open(os.getenv("GITHUB_ENV"), "a") as f:
        f.write(
            "\n".join(
                [
                    f"HUB_MATRIX_JOBS={hub_matrix_jobs}",
                    f"SUPPORT_MATRIX_JOBS={support_matrix_jobs}",
                ]
            )
        )


def pretty_print_matrix_jobs(hub_matrix_jobs, support_matrix_jobs):
    # Construct table for support chart upgrades
    support_table = Table(title="Support chart upgrades")
    support_table.add_column("Cloud Provider")
    support_table.add_column("Cluster Name")

    # Add rows
    for job in support_matrix_jobs:
        support_table.add_row(job["provider"], job["cluster_name"])

    # Construct table for hub helm chart upgrades
    hub_table = Table(title="Hub helm chart upgrades")
    hub_table.add_column("Cloud Provider")
    hub_table.add_column("Cluster Name")
    hub_table.add_column("Hub Name")

    # Add rows
    for job in hub_matrix_jobs:
        hub_table.add_row(job["provider"], job["cluster_name"], job["hub_name"])

    console = Console()
    console.print(support_table)
    console.print(hub_table)
