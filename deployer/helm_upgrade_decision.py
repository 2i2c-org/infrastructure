"""
Functions related to deciding which clusters and/or hubs need their *hub helm chart or
support helm chart upgrading depending on an input list of filenames that have been
added or modified in a GitHub Pull Request.
"""
import fnmatch
import os
from pathlib import Path

import jmespath
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML
from utils import print_colour

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
        upgrade_support_on_all_clusters (bool): Whether or not all clusters should have
            their support chart upgraded since has changes
        upgrade_all_hubs_on_all_clusters (bool): Whether or not all hubs on all clusters
            should be upgraded since a core piece of infrastructure has changed
    """
    # If any of the following filepaths have changed, we should upgrade all hubs on all clusters
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
    # If this filepath has changes, we should upgrade the support chart on all clusters
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


def get_all_cluster_yaml_files(test_env: bool = False) -> set:
    """Get a set of absolute paths to all cluster.yaml files in the repository

    Args:
        test_env (bool, optional): A flag to determine whether we are running a test
            suite or not. If True, only return the paths to cluster.yaml files under the
            'tests/' directory. If False, explicitly exclude the cluster.yaml files
            nested under the 'tests/' directory. Defaults to False.

    Returns:
        set[path obj]: A set of absolute paths to all cluster.yaml files in the repo
    """
    # Get absolute paths
    if test_env:
        # We are running a test via pytest. We only want to focus on the cluster
        # folders nested under the `tests/` folder.
        cluster_files = [
            filepath
            for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
            if "tests" in str(filepath)
        ]
    else:
        # We are NOT running a test via pytest. We want to explicitly ignore the
        # cluster folders nested under the `tests/` folder.
        cluster_files = [
            filepath
            for filepath in Path(os.getcwd()).glob("**/cluster.yaml")
            if "tests" not in str(filepath)
        ]

    # Return unique absolute paths
    return set(cluster_files)


def generate_hub_matrix_jobs(
    cluster_file,
    cluster_config,
    cluster_info,
    added_or_modified_files,
    upgrade_all_hubs_on_this_cluster=False,
    upgrade_all_hubs_on_all_clusters=False,
):
    """Generate a list of dictionaries describing which hubs on a given cluster need
    to undergo a helm upgrade based on whether their associated helm chart values
    files have been modified. To be parsed to GitHub Actions in order to generate
    parallel jobs in a matrix.

    Args:
        cluster_file (path obj): The absolute path to the cluster.yaml file of a given
            cluster
        cluster_config (dict): The cluster-wide config for a given cluster in
            dictionary format
        cluster_info (dict): A template dictionary for defining matrix jobs prepopulated
            with some info. "cluster_name": The name of the given cluster; "provider":
            the cloud provider the given cluster runs on; "reason_for_redeploy":
            what has changed in the repository to prompt a hub on this cluster to be
            redeployed.
        added_or_modified_files (set[str]): A set of all added or modified files
            provided in a GitHub Pull Requests
        upgrade_all_hubs_on_this_cluster (bool, optional): If True, generates jobs to
            upgrade all hubs on the given cluster. This is triggered when the
            cluster.yaml file itself has been modified. Defaults to False.
        upgrade_all_hubs_on_all_clusters (bool, optional): If True, generates jobs to
            upgrade all hubs on all clusters. This is triggered when common config has
            been modified, such as the basehub or daskhub helm charts. Defaults to False.

    Returns:
        list[dict]: A list of dictionaries. Each dictionary contains: the name of a
            cluster, the cloud provider that cluster runs on, the name of a hub
            deployed to that cluster, and the reason that hub needs to be redeployed.
    """
    # Empty list to store all the matrix job definitions in
    matrix_jobs = []

    # Loop over each hub on this cluster
    for hub in cluster_config.get("hubs", {}):
        if upgrade_all_hubs_on_all_clusters or upgrade_all_hubs_on_this_cluster:
            # We know we're upgrading all hubs, so just add the hub name to the list
            # of matrix jobs and move on
            matrix_job = cluster_info.copy()
            matrix_job["hub_name"] = hub["name"]

            if upgrade_all_hubs_on_all_clusters:
                matrix_job[
                    "reason_for_redeploy"
                ] = "Core infrastructure has been modified"

            matrix_jobs.append(matrix_job)

        else:
            # Read in this hub's helm chart values files from the cluster.yaml file
            values_files = [
                cluster_file.parent.joinpath(values_file)
                for values_file in hub.get("helm_chart_values_files", {})
            ]
            # Establish if any of this hub's helm chart values files have been
            # modified
            intersection = added_or_modified_files.intersection(values_files)

            if intersection:
                # If at least one of the helm chart values files associated with
                # this hub has been modified, add it to list of matrix jobs to be
                # upgraded
                matrix_job = cluster_info.copy()
                matrix_job["hub_name"] = hub["name"]
                matrix_job[
                    "reason_for_redeploy"
                ] = "Following helm chart values files were modified: " + ", ".join(
                    [path.name for path in intersection]
                )
                matrix_jobs.append(matrix_job)

    return matrix_jobs


def generate_support_matrix_jobs(
    cluster_file,
    cluster_config,
    cluster_info,
    added_or_modified_files,
    upgrade_support_on_this_cluster=False,
    upgrade_support_on_all_clusters=False,
):
    """Generate a list of dictionaries describing which clusters need to undergo a helm
    upgrade of their support chart based on whether their associated support chart
    values files have been modified. To be parsed to GitHub Actions in order to generate
    jobs in a matrix.

    Args:
        cluster_file (path obj): The absolute path to the cluster.yaml file of a given
            cluster
        cluster_config (dict): The cluster-wide config for a given cluster in
            dictionary format
        cluster_info (dict): A template dictionary for defining matrix jobs prepopulated
            with some info. "cluster_name": The name of the given cluster; "provider":
            the cloud provider the given cluster runs on; "reason_for_redeploy":
            what has changed in the repository to prompt the support chart for this
            cluster to be redeployed.
        added_or_modified_files (set[str]): A set of all added or modified files
            provided in a GitHub Pull Requests
        upgrade_support_on_this_cluster (bool, optional): If True, generates jobs to
            update the support chart on the given cluster. This is triggered when the
            cluster.yaml file itself is modified. Defaults to False.
        upgrade_support_on_all_clusters (bool, optional): If True, generates jobs to
            update the support chart on all clusters. This is triggered when common
            config has been modified in the support helm chart. Defaults to False.

    Returns:
        list[dict]: A list of dictionaries. Each dictionary contains: the name of a
            cluster, the cloud provider that cluster runs on, a Boolean indicating if
            the support chart should be upgraded, and a reason why the support chart
            needs upgrading.
    """
    cluster_info["reason_for_support_redeploy"] = cluster_info.pop(
        "reason_for_redeploy"
    )

    # Empty list to store the matrix definitions in
    matrix_jobs = []

    # Double-check that support is defined for this cluster.
    support_config = cluster_config.get("support", {})
    if support_config:
        if upgrade_support_on_all_clusters or upgrade_support_on_this_cluster:
            # We know we're upgrading support on all clusters, so just add the cluster
            # name to the list of matrix jobs and move on
            matrix_job = cluster_info.copy()
            matrix_job["upgrade_support"] = "true"

            if upgrade_support_on_all_clusters:
                matrix_job[
                    "reason_for_support_redeploy"
                ] = "Support helm chart has been modified"

            matrix_jobs.append(matrix_job)

        else:
            # Have the related support values files for this cluster been modified?
            values_files = [
                cluster_file.parent.joinpath(values_file)
                for values_file in support_config.get("helm_chart_values_files", {})
            ]
            intersection = added_or_modified_files.intersection(values_files)

            if intersection:
                matrix_job = cluster_info.copy()
                matrix_job["upgrade_support"] = "true"
                matrix_job[
                    "reason_for_support_redeploy"
                ] = "Following helm chart values files were modified: " + ", ".join(
                    [path.name for path in intersection]
                )
                matrix_jobs.append(matrix_job)

    else:
        print(f"No support defined for cluster: {cluster_info['cluster_name']}")

    return matrix_jobs


def move_staging_jobs_to_staging_matrix(
    all_hub_matrix_jobs: list, support_and_staging_matrix_jobs: list
) -> (list, list):
    """This function's first argument is a list of dictionary jobs calculated for
    hubs by the generate_hub_matrix_job function and filters them based on whether
    "staging" appears in the "hub_name" field or not. The list of production hub jobs,
    those without "staging" in their name, are returned unchanged as the first argument.

    The second argument is a list of dictionary jobs to upgrade the support chart on
    clusters that require it. The filtered list of staging hubs, those with "staging"
    in their name, is used to update these jobs with information to upgrade the staging
    hub for that cluster. If a job for a cluster matching a staging hub does not already
    exist in support_and_staging_matrix_jobs, one is created that *doesn't* also upgrade
    the support chart since this is the reason the job doesn't exist in the first place.

    Updated support_and_staging_matrix_jobs with the following properties are returned
    as the second argument. Note: string representations of booleans are required to be
    recognised by the GitHub Actions runner.

    {
        "cluster_name": str,
        "provider": str,
        "upgrade_support": str(bool),
        "reason_for_support_redeploy_: str,
        "upgrade_staging": str(bool),
        "reason_for_staging_redeploy_: str,
    }

    Args:
        all_hub_matrix_jobs (list[dict]): A list of dictionaries representing matrix
            jobs to upgrade deployed hubs as identified by the generate_hub_matrix_jobs
            function.
        support_and_staging_matrix_jobs (list[dict]): A list of dictionaries
            representing matrix jobs to upgrade the support chart for clusters as
            identified by the generate_support_matrix_jobs function.

    Returns:
        prod_hub_matrix_jobs (list[dict]): A list of dictionaries representing matrix
            jobs to upgrade all production hubs, i.e., those without "staging" in their
            name.
        support_and_staging_matrix_jobs (list[dict]): A list of dictionaries representing
            matrix jobs to upgrade the support chart and staging hub on clusters that
            require it.
    """
    # Separate the jobs for hubs with "staging" in their name (including "dask-staging")
    # from those without staging in their name
    staging_hub_jobs = [
        job for job in all_hub_matrix_jobs if "staging" in job["hub_name"]
    ]
    prod_hub_matrix_jobs = [
        job for job in all_hub_matrix_jobs if "staging" not in job["hub_name"]
    ]

    # Loop over each job for a staging hub
    for staging_job in staging_hub_jobs:
        # Find a job in support_and_staging_matrix_jobs that is for the same cluster as
        # the current staging hub job
        job_idx = next(
            (
                idx
                for (idx, job) in enumerate(support_and_staging_matrix_jobs)
                if staging_job["cluster_name"] == job["cluster_name"]
            ),
            None,
        )

        if job_idx is not None:
            # Update the matching job in support_and_staging_matrix_jobs to hold
            # information related to upgrading the staging hub
            support_and_staging_matrix_jobs[job_idx]["upgrade_staging"] = "true"
            support_and_staging_matrix_jobs[job_idx][
                "reason_for_staging_redeploy"
            ] = staging_job["reason_for_redeploy"]
        else:
            # A job with a matching cluster name doesn't exist, this is because its
            # support chart doesn't need upgrading. We create a new job in that will
            # upgrade the staging deployment for this cluster, but not the support
            # chart.
            new_job = {
                "cluster_name": staging_job["cluster_name"],
                "provider": staging_job["provider"],
                "upgrade_staging": "true",
                "reason_for_staging_redeploy": staging_job["reason_for_redeploy"],
                "upgrade_support": "false",
                "reason_for_support_redeploy": "",
            }
            support_and_staging_matrix_jobs.append(new_job)

    return prod_hub_matrix_jobs, support_and_staging_matrix_jobs


        # Double-check that support is defined for this cluster.
        support_config = cluster_config.get("support", {})
        if support_config:
            if upgrade_support_on_all_clusters:
                # We know we're upgrading support on all clusters, so just add the cluster name to the list
                # of matrix jobs and move on
                matrix_job = cluster_info.copy()
                matrix_job[
                    "reason_for_redeploy"
                ] = "Support helm chart has been modified"
                matrix_jobs.append(matrix_job)
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
                    matrix_job = cluster_info.copy()

                    if len(support_values_intersection) > 0:
                        matrix_job["reason_for_redeploy"] = (
                            "Following helm chart values files were modified:\n- "
                            + "\n- ".join(support_values_intersection)
                        )
                    elif len(cluster_yaml_intersection) > 0:
                        matrix_job[
                            "reason_for_redeploy"
                        ] = "cluster.yaml file was modified"

                    matrix_jobs.append(matrix_job)
        else:
            print_colour(
                f"No support defined for cluster: {cluster_config.get('name', {})}"
            )

    return matrix_jobs


def update_github_env(support_matrix_jobs, staging_hub_matrix_jobs, prod_hub_matrix_jobs):
    """Update the GITHUB_ENV environment with two new variables describing the matrix
    jobs that need to be run in order to update the support charts and hubs that have
    been modified.

    Args:
        support_matrix_jobs (list[dict]):  A list of dictionaries which describe the
            set of matrix jobs required to upgrade only the support chart on clusters
            whose config has been modified.
        staging_hub_matrix_jobs (list[dict]): A list of dictionaries which describe the
            set of matrix jobs required to upgrade only the staging hubs on clusters
            whose config has been modified.
        prod_hub_matrix_jobs (list[dict]): A list of dictionaries which describe the
            set of matrix jobs required to upgrade only the production hubs on clusters
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
                    f"SUPPORT_MATRIX_JOBS={support_matrix_jobs}",
                    f"STAGING_HUB_MATRIX_JOBS={staging_hub_matrix_jobs}",
                    f"PROD_HUB_MATRIX_JOBS={prod_hub_matrix_jobs}",
                ]
            )
        )


def pretty_print_matrix_jobs(support_matrix_jobs, staging_hub_matrix_jobs, prod_hub_matrix_jobs):
    # Construct table for support chart upgrades
    support_table = Table(title="Support chart upgrades")
    support_table.add_column("Cloud Provider")
    support_table.add_column("Cluster Name")
    support_table.add_column("Reason for Redeploy")

    # Add rows
    for job in support_matrix_jobs:
        support_table.add_row(
            job["provider"], job["cluster_name"], job["reason_for_redeploy"]
        )

    # Construct table for staging hub helm chart upgrades
    staging_hub_table = Table(title="Hub helm chart upgrades - Staging")
    staging_hub_table.add_column("Cloud Provider")
    staging_hub_table.add_column("Cluster Name")
    staging_hub_table.add_column("Hub Name")
    staging_hub_table.add_column("Reason for Redeploy")

    # Add rows
    for job in staging_hub_matrix_jobs:
        staging_hub_table.add_row(
            job["provider"],
            job["cluster_name"],
            job["hub_name"],
            job["reason_for_redeploy"],
        )

    # Construct table for production hub helm chart upgrades
    prod_hub_table = Table(title="Hub helm chart upgrades")
    prod_hub_table.add_column("Cloud Provider")
    prod_hub_table.add_column("Cluster Name")
    prod_hub_table.add_column("Hub Name")
    prod_hub_table.add_column("Reason for Redeploy")

    # Add rows
    for job in prod_hub_matrix_jobs:
        prod_hub_table.add_row(
            job["provider"],
            job["cluster_name"],
            job["hub_name"],
            job["reason_for_redeploy"],
        )

    console = Console()
    console.print(support_table)
    console.print(staging_hub_table)
    console.print(prod_hub_table)
