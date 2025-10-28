"""
Actions available when deploying many JupyterHubs to many Kubernetes clusters
"""

import base64
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest
import typer
from ruamel.yaml import YAML

from deployer.cli_app import CONTINUOUS_DEPLOYMENT, app
from deployer.commands.validate.config import (
    cleanup_values_schema_json,
)
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.commands.validate.config import (
    get_chart_dir,
)
from deployer.commands.validate.config import support_config as validate_support_config
from deployer.commands.validate.config import (
    validate_authenticator_config,
    validate_hub_config,
)
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
    get_decrypted_file,
)
from deployer.utils.rendering import print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
def deploy_support(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    # cert-manager versions at https://cert-manager.io/docs/release-notes/,
    # update to latest when updating and make sure to read upgrade notes.
    #
    # "kubectl apply" will be done on CRDs but sometimes more is needed.
    #
    cert_manager_version: str = typer.Option(
        "v1.15.3", help="Version of cert-manager to install"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="When present, the `--debug` flag will be passed to the `helm upgrade` command.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="When present, the `--dry-run` flag will be passed to the `helm upgrade` command.",
    ),
):
    """
    Deploy support components to a cluster
    """
    validate_cluster_config(cluster_name)
    validate_support_config(cluster_name)

    cluster = Cluster.from_name(cluster_name)

    if cluster.support:
        with cluster.auth():
            cluster.deploy_support(
                cert_manager_version=cert_manager_version,
                debug=debug,
                dry_run=dry_run,
            )


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
def deploy(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        None,
        help="Name of hub to operate deploy. Omit to deploy all hubs on the cluster",
    ),
    dask_gateway_version: str = typer.Option(
        "2024.1.0", help="Version of dask-gateway to install CRDs for"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="""When present, the `--debug` flag will be passed to the `helm upgrade` command.""",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="""When present, the `--dry-run` flag will be passed to the `helm upgrade` command.""",
    ),
    skip_refresh: bool = typer.Option(
        False,
        "--skip-refresh",
        help="""When present, the helm charts and schemas will not be updated.""",
    ),
):
    """
    Deploy one or more hubs in a given cluster
    """

    print_colour(f"Validating cluster configuration for {cluster_name}...")
    validate_cluster_config(cluster_name)
    cluster = Cluster.from_name(cluster_name)
    with cluster.auth():
        if hub_name:
            hubs = [h for h in cluster.hubs if h.spec["name"] == hub_name]
        else:
            hubs = cluster.hubs
        for i, hub in enumerate(hubs):
            default_chart_dir = HELM_CHARTS_DIR / hub.spec["helm_chart"]
            chart_override = hub.spec.get("chart_override", None)
            chart_override_path = (
                hub.cluster.config_dir / chart_override if chart_override else None
            )
            with get_chart_dir(
                default_chart_dir, chart_override, chart_override_path
            ) as chart_dir:
                print_colour(
                    f"{i + 1} / {len(hubs)}: Validating non-encrypted hub values files for {hub.spec['name']}..."
                )
                validate_hub_config(
                    cluster_name, hub.spec["name"], chart_dir, skip_refresh
                )
                print_colour(
                    f"{i + 1} / {len(hubs)}: Validating authenticator config for {hub.spec['name']}..."
                )
                validate_authenticator_config(
                    cluster_name, hub.spec["name"], chart_dir, skip_refresh
                )

                print_colour(
                    f"{i + 1} / {len(hubs)}: Deploying hub {hub.spec['name']}..."
                )
                hub.deploy(chart_dir, dask_gateway_version, debug, dry_run)
                cleanup_values_schema_json(chart_dir)


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
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
    cluster = Cluster.from_name(cluster_name)

    # Find the hub's config
    hub_indx = [
        index for (index, h) in enumerate(cluster.hubs) if h.spec["name"] == hub_name
    ]
    if len(hub_indx) == 1:
        hub = cluster.hubs[hub_indx[0]]
    elif len(hub_indx) > 1:
        print_colour("ERROR: More than one hub with this name found!")
        sys.exit(1)
    elif len(hub_indx) == 0:
        print_colour("ERROR: No hubs with this name found!")
        sys.exit(1)

    # Skip the regular hub health check for hubs with binderhub ui that are not authenticated
    if hub.binderhub_ui and hub.authenticator == "null":
        print_colour(
            f"Testing {hub.spec['name']} is not yet supported. Skipping ...",
            "yellow",
        )
        return

    print_colour(f"Running hub health check for {hub.spec['name']}...")

    # Check if this hub has a domain override file. If yes, apply override.
    if "domain_override_file" in hub.spec.keys():
        domain_override_file = hub.spec["domain_override_file"]

        with get_decrypted_file(
            hub.cluster.config_dir / domain_override_file
        ) as decrypted_path:
            with open(decrypted_path) as f:
                domain_override_config = yaml.load(f)

        hub.spec["domain"] = domain_override_config["domain"]

    # Retrieve hub's URL
    hub_url = f"https://{hub.spec['domain']}"

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
        "deployer/health_check_tests",
        f"--hub-url={hub_url}",
        f"--api-token={service_api_token}",
        f"--hub-type={hub.spec['helm_chart']}",
    ]

    if hub.type == "daskhub" and check_dask_scaling:
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
