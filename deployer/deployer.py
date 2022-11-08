"""
Actions available when deploying many JupyterHubs to many Kubernetes clusters
"""
import base64
import json
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import typer
from ruamel.yaml import YAML

from .auth import KeyProvider
from .cli_app import app
from .cluster import Cluster
from .config_validation import (
    validate_authenticator_config,
    validate_cluster_config,
    validate_hub_config,
    validate_support_config,
)
from .file_acquisition import find_absolute_path_to_cluster_file, get_decrypted_file
from .helm_upgrade_decision import (
    assign_staging_jobs_for_missing_clusters,
    discover_modified_common_files,
    ensure_support_staging_jobs_have_correct_keys,
    generate_hub_matrix_jobs,
    generate_support_matrix_jobs,
    get_all_cluster_yaml_files,
    move_staging_hubs_to_staging_matrix,
    pretty_print_matrix_jobs,
)
from .utils import create_markdown_comment, print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)
helm_charts_dir = Path(__file__).parent.parent.joinpath("helm-charts")


@app.command()
def use_cluster_credentials(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
):
    """
    Pop a new shell authenticated to the given cluster using the deployer's credentials
    """
    # This function is to be used with the `use-cluster-credentials` CLI
    # command only - it is not used by the rest of the deployer codebase.
    validate_cluster_config(cluster_name)

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    # Cluster.auth() method has the context manager decorator so cannot call
    # it like a normal function
    with cluster.auth():
        # This command will spawn a new shell with all the env vars (including
        # KUBECONFIG) inherited, and once you quit that shell the python program
        # will resume as usual.
        # TODO: Figure out how to change the PS1 env var of the spawned shell
        # to change the prompt to f"cluster-{cluster.spec['name']}". This will
        # make it visually clear that the user is now operating in a different
        # shell.
        subprocess.check_call([os.environ["SHELL"], "-l"])


@app.command()
def deploy_support(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    cert_manager_version: str = typer.Option(
        "v1.8.2", help="Version of cert-manager to install"
    ),
):
    """
    Deploy support components to a cluster
    """
    validate_cluster_config(cluster_name)
    validate_support_config(cluster_name)

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    if cluster.support:
        with cluster.auth():
            cluster.deploy_support(cert_manager_version=cert_manager_version)


@app.command()
def deploy_grafana_dashboards(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on")
):
    """
    Deploy JupyterHub dashboards to grafana set up in the given cluster

    Grafana dashboards and deployment mechanism are maintained at
    https://github.com/jupyterhub/grafana-dashboards
    """
    validate_cluster_config(cluster_name)
    validate_support_config(cluster_name)

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    # If grafana support chart is not deployed, then there's nothing to do
    if not cluster.support:
        print_colour(
            "Support chart has not been deployed. Skipping Grafana dashboards deployment..."
        )
        return

    grafana_token_file = (config_file_path.parent).joinpath(
        "enc-grafana-token.secret.yaml"
    )

    # Read the cluster specific secret grafana token file
    with get_decrypted_file(grafana_token_file) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # Check GRAFANA_TOKEN exists in the secret config file before continuing
    if "grafana_token" not in config.keys():
        raise ValueError(
            f"`grafana_token` not provided in secret file! Please add it and try again: {grafana_token_file}"
        )

    # FIXME: We assume grafana_url and uses_tls config will be defined in the first
    #        file listed under support.helm_chart_values_files.
    support_values_file = cluster.support.get("helm_chart_values_files", [])[0]
    with open(config_file_path.parent.joinpath(support_values_file)) as f:
        support_values_config = yaml.load(f)

    # Get the url where grafana is running from the support values file
    grafana_url = (
        support_values_config.get("grafana", {}).get("ingress", {}).get("hosts", {})
    )
    uses_tls = (
        support_values_config.get("grafana", {}).get("ingress", {}).get("tls", {})
    )

    if not grafana_url:
        print_colour(
            "Couldn't find `config.grafana.ingress.hosts`. Skipping Grafana dashboards deployment..."
        )
        return

    grafana_url = (
        f"https://{grafana_url[0]}" if uses_tls else f"http://{grafana_url[0]}"
    )

    # Use the jupyterhub/grafana-dashboards deployer to deploy the dashboards to this cluster's grafana
    print_colour("Cloning jupyterhub/grafana-dashboards...")

    dashboards_dir = "grafana_dashboards"

    subprocess.check_call(
        [
            "git",
            "clone",
            "https://github.com/jupyterhub/grafana-dashboards",
            dashboards_dir,
        ]
    )

    # We need the existing env too for the deployer to be able to find jssonnet and grafonnet
    deploy_env = os.environ.copy()
    deploy_env.update({"GRAFANA_TOKEN": config["grafana_token"]})

    try:
        print_colour(f"Deploying grafana dashboards to {cluster_name}...")
        subprocess.check_call(
            ["./deploy.py", grafana_url], env=deploy_env, cwd=dashboards_dir
        )

        print_colour(f"Done! Dashboards deployed to {grafana_url}.")
    finally:
        # Delete the directory where we cloned the repo.
        # The deployer cannot call jsonnet to deploy the dashboards if using a temp directory here.
        # Might be because opening more than once of a temp file is tried
        # (https://docs.python.org/3.8/library/tempfile.html#tempfile.NamedTemporaryFile)
        shutil.rmtree(dashboards_dir)


@app.command()
def deploy(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        None,
        help="Name of hub to operate deploy. Omit to deploy all hubs on the cluster",
    ),
    config_path: str = typer.Option(
        "shared/deployer/enc-auth-providers-credentials.secret.yaml",
        help="File to read secret deployment config from",
    ),
    dask_gateway_version: str = typer.Option(
        "v2022.10.0", help="Version of dask-gateway to install CRDs for"
    ),
):
    """
    Deploy one or more hubs in a given cluster
    """
    validate_cluster_config(cluster_name)
    validate_hub_config(cluster_name, hub_name)
    validate_authenticator_config(cluster_name, hub_name)

    with get_decrypted_file(config_path) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # Most of our hubs use Auth0 for Authentication. This lets us programmatically
    # determine what auth provider each hub uses - GitHub, Google, etc. Without
    # this, we'd have to manually generate credentials for each hub - and we
    # don't want to do that. Auth0 domains are tied to a account, and
    # this is our auth0 domain for the paid account that 2i2c has.
    auth0 = config["auth0"]

    k = KeyProvider(auth0["domain"], auth0["client_id"], auth0["client_secret"])

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    with cluster.auth():
        hubs = cluster.hubs
        if hub_name:
            hub = next((hub for hub in hubs if hub.spec["name"] == hub_name), None)
            print_colour(f"Deploying hub {hub.spec['name']}...")
            hub.deploy(k, dask_gateway_version)
        else:
            for i, hub in enumerate(hubs):
                print_colour(
                    f"{i+1} / {len(hubs)}: Deploying hub {hub.spec['name']}..."
                )
                hub.deploy(k, dask_gateway_version)


@app.command()
def generate_helm_upgrade_jobs(
    changed_filepaths: str = typer.Argument(
        ..., help="Comma delimited list of files that have changed"
    )
):
    """
    Analyse added or modified files from a GitHub Pull Request and decide which
    clusters and/or hubs require helm upgrades to be performed for their *hub helm
    charts or the support helm chart.
    """
    changed_filepaths = changed_filepaths.split(",")
    (
        upgrade_support_on_all_clusters,
        upgrade_all_hubs_on_all_clusters,
    ) = discover_modified_common_files(changed_filepaths)

    # Convert changed filepaths into absolute Posix Paths
    root_dir = Path(__file__).parent.parent
    changed_filepaths = [root_dir.joinpath(filepath) for filepath in changed_filepaths]

    # Get a list of filepaths to all cluster.yaml files in the repo
    cluster_files = get_all_cluster_yaml_files()

    # Empty lists to store job definitions in
    prod_hub_matrix_jobs = []
    support_and_staging_matrix_jobs = []

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
        prod_hub_matrix_jobs.extend(
            generate_hub_matrix_jobs(
                cluster_file,
                cluster_config,
                cluster_info,
                set(changed_filepaths),
                upgrade_all_hubs_on_this_cluster=upgrade_all_hubs_on_this_cluster,
                upgrade_all_hubs_on_all_clusters=upgrade_all_hubs_on_all_clusters,
            )
        )

        # Generate a job matrix for support chart upgrades
        support_and_staging_matrix_jobs.extend(
            generate_support_matrix_jobs(
                cluster_file,
                cluster_config,
                cluster_info,
                set(changed_filepaths),
                upgrade_support_on_this_cluster=upgrade_support_on_this_cluster,
                upgrade_support_on_all_clusters=upgrade_support_on_all_clusters,
            )
        )

    # Clean up the matrix jobs
    (
        prod_hub_matrix_jobs,
        support_and_staging_matrix_jobs,
    ) = move_staging_hubs_to_staging_matrix(
        prod_hub_matrix_jobs, support_and_staging_matrix_jobs
    )
    support_and_staging_matrix_jobs = ensure_support_staging_jobs_have_correct_keys(
        support_and_staging_matrix_jobs, prod_hub_matrix_jobs
    )
    support_and_staging_matrix_jobs = assign_staging_jobs_for_missing_clusters(
        support_and_staging_matrix_jobs, prod_hub_matrix_jobs
    )

    # Pretty print the jobs using rich
    pretty_print_matrix_jobs(prod_hub_matrix_jobs, support_and_staging_matrix_jobs)

    # The existence of the CI environment variable is an indication that we are running
    # in an GitHub Actions workflow
    # https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#example-defining-outputs-for-a-job
    # This will avoid errors trying to set CI output variables in an environment that
    # doesn't exist.
    ci_env = os.environ.get("CI", False)
    # The use of ::set-output was deprecated as per the below blog post and
    # instead we share variables between steps/jobs by writing them to GITHUB_ENV:
    # https://github.blog/changelog/2022-10-11-github-actions-deprecating-save-state-and-set-output-commands/
    # More info on GITHUB_ENV: https://docs.github.com/en/actions/learn-github-actions/environment-variables
    env_file = os.getenv("GITHUB_ENV")
    if ci_env:
        # Add these matrix jobs as environment variables for use in another job
        with open(env_file, "a") as f:
            f.write(f"prod-hub-matrix-jobs={json.dumps(prod_hub_matrix_jobs)}")
            f.write("\n")
            f.write(
                f"support-and-staging-matrix-jobs={json.dumps(support_and_staging_matrix_jobs)}"
            )

        # Don't bother generating a comment if both of the matrices are empty
        if support_and_staging_matrix_jobs or prod_hub_matrix_jobs:
            # Generate Markdown tables from the job matrices and write them to a file
            # for use in another job
            create_markdown_comment(
                support_and_staging_matrix_jobs, prod_hub_matrix_jobs
            )


@app.command()
def run_hub_health_check(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    check_dask_scaling: bool = typer.Option(
        False, help="Check that dask workers can be scaled"
    ),
):
    """
    Run a health check on a given hub on a given cluster. Optionally check scaling
    of dask workers if the hub is a daskhub.
    """
    # Read in the cluster.yaml file
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    # Find the hub's config
    hub_indx = [
        indx for (indx, h) in enumerate(cluster.hubs) if h.spec["name"] == hub_name
    ]
    if len(hub_indx) == 1:
        hub = cluster.hubs[hub_indx[0]]
    elif len(hub_indx) > 1:
        print_colour("ERROR: More than one hub with this name found!")
        sys.exit(1)
    elif len(hub_indx) == 0:
        print_colour("ERROR: No hubs with this name found!")
        sys.exit(1)

    print_colour(f"Running hub health check for {hub.spec['name']}...")

    # Check if this hub has a domain override file. If yes, apply override.
    if "domain_override_file" in hub.spec.keys():
        domain_override_file = hub.spec["domain_override_file"]

        with get_decrypted_file(
            hub.cluster.config_path.joinpath(domain_override_file)
        ) as decrypted_path:
            with open(decrypted_path) as f:
                domain_override_config = yaml.load(f)

        hub.spec["domain"] = domain_override_config["domain"]

    # Retrieve hub's URL
    hub_url = f'https://{hub.spec["domain"]}'

    # Read in the service api token from a k8s Secret in the k8s cluster
    with cluster.auth():
        try:
            service_api_token_b64encoded = subprocess.check_output(
                [
                    "kubectl",
                    "get",
                    "secrets",
                    "hub",
                    f"--namespace={hub.spec['name']}",
                    r"--output=jsonpath={.data['hub\.services\.hub-health\.apiToken']}",
                ],
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"Failed to acquire a JupyterHub API token for the hub-health service: {e.stdout}"
            )
        service_api_token = base64.b64decode(service_api_token_b64encoded).decode()

    # On failure, pytest prints out params to the test that failed.
    # This can contain sensitive info - so we hide stderr
    # FIXME: Don't use pytest - just call a function instead
    #
    # Show errors locally but redirect on CI
    gh_ci = os.environ.get("CI", "false")
    pytest_args = [
        "-q",
        "deployer/tests",
        f"--hub-url={hub_url}",
        f"--api-token={service_api_token}",
        f"--hub-type={hub.spec['helm_chart']}",
    ]

    if (hub.spec["helm_chart"] == "daskhub") and check_dask_scaling:
        pytest_args.append("--check-dask-scaling")

    if gh_ci == "true":
        print_colour("Testing on CI, not printing output")
        with open(os.devnull, "w") as dn, redirect_stderr(dn), redirect_stdout(dn):
            exit_code = pytest.main(pytest_args)
    else:
        print_colour("Testing locally, do not redirect output")
        exit_code = pytest.main(pytest_args)
    if exit_code != 0:
        print("Health check failed!", file=sys.stderr)
        sys.exit(exit_code)
    else:
        print_colour("Health check succeeded!")


@app.command()
def validate(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
):
    """
    Validate cluster.yaml and non-encrypted helm config for given hub
    """
    validate_cluster_config(cluster_name)
    validate_support_config(cluster_name)
    validate_hub_config(cluster_name, hub_name)
    validate_authenticator_config(cluster_name, hub_name)
