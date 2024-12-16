import json
import os

import typer
from ruamel.yaml import YAML

from deployer.cli_app import generate_app
from deployer.utils.file_acquisition import REPO_ROOT_PATH, get_all_cluster_yaml_files
from deployer.utils.rendering import create_markdown_comment, print_colour

from .decision import (
    assign_staging_jobs_for_missing_clusters,
    discover_modified_common_files,
    ensure_support_staging_jobs_have_correct_keys,
    generate_hub_matrix_jobs,
    generate_support_matrix_jobs,
    pretty_print_matrix_jobs,
)

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@generate_app.command()
def helm_upgrade_jobs(
    changed_filepaths: str = typer.Argument(
        ..., help="Comma delimited list of files that have changed"
    ),
    pr_labels: str = typer.Argument(
        "[]",
        help="JSON formatted list of PR labels, where 'deployer:skip-deploy', 'deployer:skip-deploy-hubs', 'deployer:deploy-support', and 'deployer:deploy-hubs' are respected.",
    ),
):
    """
    Analyze added or modified files and labels from a GitHub Pull Request and
    decide which clusters and/or hubs require helm upgrades to be performed for
    their *hub helm charts or the support helm chart.
    """
    pr_labels = json.loads(pr_labels)

    changed_filepaths = changed_filepaths.split(",")
    (
        upgrade_support_on_all_clusters,
        upgrade_all_hubs_on_all_clusters,
    ) = discover_modified_common_files(changed_filepaths)

    if "deployer:deploy-support" in pr_labels:
        upgrade_support_on_all_clusters = True
    if "deployer:deploy-hubs" in pr_labels:
        upgrade_all_hubs_on_all_clusters = True

    # Convert changed filepaths into absolute Posix Paths
    changed_filepaths = [
        REPO_ROOT_PATH.joinpath(filepath) for filepath in changed_filepaths
    ]

    # Get a list of filepaths to all cluster.yaml files in the repo
    cluster_files = get_all_cluster_yaml_files()

    # Empty lists to store job definitions in
    support_matrix_jobs = []
    staging_hub_matrix_jobs = []
    prod_hub_matrix_jobs = []

    for cluster_file in cluster_files:
        # Read in the cluster.yaml file
        with open(cluster_file) as f:
            cluster_config = yaml.load(f)

        # Get cluster's name and its cloud provider
        cluster_name = cluster_config.get("name", {})
        provider = cluster_config.get("provider", {})

        # Generate template dictionary for all jobs associated with this cluster
        cluster_info = {
            "cluster_name": cluster_name,
            "provider": provider,
            "reason_for_redeploy": "",
        }

        # Check if this cluster file has been modified. If so, set boolean flags to True
        intersection = set(changed_filepaths).intersection([str(cluster_file)])
        if intersection:
            print_colour(
                f"This cluster.yaml file has been modified. Generating jobs to upgrade all hubs and the support chart on THIS cluster: {cluster_name}"
            )
            upgrade_all_hubs_on_this_cluster = True
            upgrade_support_on_this_cluster = True
            cluster_info["reason_for_redeploy"] = "cluster.yaml file was modified"
        else:
            upgrade_all_hubs_on_this_cluster = False
            upgrade_support_on_this_cluster = False

        # Generate a job matrix of all hubs that need upgrading on this cluster
        staging_hubs, prod_hubs = (
            generate_hub_matrix_jobs(
                cluster_file,
                cluster_config,
                cluster_info,
                set(changed_filepaths),
                pr_labels,
                upgrade_all_hubs_on_this_cluster=upgrade_all_hubs_on_this_cluster,
                upgrade_all_hubs_on_all_clusters=upgrade_all_hubs_on_all_clusters,
            )
        )
        staging_hub_matrix_jobs.extend(staging_hubs)
        prod_hub_matrix_jobs.extend(prod_hubs)

        # Generate a job matrix for support chart upgrades
        support_matrix_jobs.extend(
            generate_support_matrix_jobs(
                cluster_file,
                cluster_config,
                cluster_info,
                set(changed_filepaths),
                pr_labels,
                upgrade_support_on_this_cluster=upgrade_support_on_this_cluster,
                upgrade_support_on_all_clusters=upgrade_support_on_all_clusters,
            )
        )

    # Clean up the matrix jobs
    # support_and_staging_matrix_jobs = ensure_support_staging_jobs_have_correct_keys(
    #     support_and_staging_matrix_jobs, prod_hub_matrix_jobs
    # )
    staging_matrix_jobs = assign_staging_jobs_for_missing_clusters(staging_hub_matrix_jobs, prod_hub_matrix_jobs)
    # Pretty print the jobs using rich
    pretty_print_matrix_jobs(support_matrix_jobs, staging_hub_matrix_jobs, prod_hub_matrix_jobs)

    # The existence of the CI environment variable is an indication that we are running
    # in an GitHub Actions workflow
    # https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#example-defining-outputs-for-a-job
    # This will avoid errors trying to set CI output variables in an environment that
    # doesn't exist.
    ci_env = os.environ.get("CI", False)
    # More info on GITHUB_OUTPUT: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/passing-information-between-jobs
    output_file = os.getenv("GITHUB_OUTPUT")
    if ci_env:
        # Add these matrix jobs as output variables for use in another job
        with open(output_file, "a") as f:
            f.write(f"prod-hub-matrix-jobs={json.dumps(prod_hub_matrix_jobs)}\n")
            f.write(
                f"support-and-staging-matrix-jobs={json.dumps(support_and_staging_matrix_jobs)}\n"
            )

        # Don't bother generating a comment if both of the matrices are empty
        if support_and_staging_matrix_jobs or prod_hub_matrix_jobs:
            # Generate Markdown tables from the job matrices and write them to a file
            # for use in another job
            create_markdown_comment(
                support_and_staging_matrix_jobs, prod_hub_matrix_jobs
            )
