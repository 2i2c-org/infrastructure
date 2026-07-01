"""
Actions available when deploying many JupyterHubs to many Kubernetes clusters
"""

import asyncio
import base64
import subprocess
import sys

import typer
from ruamel.yaml import YAML

from deployer.cli_app import CONTINUOUS_DEPLOYMENT, app
from deployer.commands.validate.config import (
    cleanup_values_schema_json,
)
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.commands.validate.config import get_chart_dir
from deployer.commands.validate.config import support_config as validate_support_config
from deployer.commands.validate.config import (
    validate_authenticator_config,
    validate_hub_config,
)
from deployer.health_check_tests.test_hub_health import test_hub_healthy
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
    REPO_ROOT_PATH,
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
        "v1.20.2", help="Version of cert-manager to install"
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
    skip_crds: bool = typer.Option(
        False,
        "--skip-crds",
        help="When present, the `--skip-crds` flag will cause the deployer to skip external CRD deployments.",
    ),
):
    """
    Deploy support components to a cluster
    """
    validate_cluster_config(cluster_name)
    validate_support_config(cluster_name, False, False)

    cluster = Cluster.from_name(cluster_name)

    if cluster.support:
        with cluster.auth():
            cluster.deploy_support(
                cert_manager_version=cert_manager_version,
                debug=debug,
                dry_run=dry_run,
                skip_crds=skip_crds,
            )


def determine_dask_gateway_version(chart_dir):
    # Function to determine what dask-gateway version to install CRDs for
    # We check the Chart file directly to get this info
    chart_config = chart_dir / "Chart.yaml"
    with open(chart_config, "r+") as f:
        config = yaml.load(f)
        for dep in config["dependencies"]:
            if dep["name"] == "dask-gateway":
                return dep["version"]


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
def deploy(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        None,
        help="Name of hub to operate deploy. Omit to deploy all hubs on the cluster",
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
        progress_str = ""
        for i, hub in enumerate(hubs):
            default_chart_dir = HELM_CHARTS_DIR / hub.spec["helm_chart"]
            chart_override = hub.spec.get("chart_override", None)
            if chart_override and "/" in chart_override:
                # It's probably a path relative to the repo root
                chart_override_path = REPO_ROOT_PATH / chart_override
                chart_override = chart_override.split("/")[-1]
            else:
                chart_override_path = (
                    hub.cluster.config_dir / chart_override if chart_override else None
                )
            with get_chart_dir(
                default_chart_dir,
                chart_override,
                chart_override_path,
                hub.legacy_daskhub,
            ) as chart_dir:
                if hub.legacy_daskhub:
                    dask_gateway_version = determine_dask_gateway_version(
                        chart_dir.parent / "basehub"
                    )
                else:
                    dask_gateway_version = determine_dask_gateway_version(chart_dir)
                print_colour(
                    f"Installing CRDs for dask-gateway version {dask_gateway_version}",
                    "yellow",
                )

                if chart_override_path:
                    print_colour(
                        f"Deploying a custom helm chart for a {hub.spec['helm_chart']} from {chart_dir}, for {chart_override_path}",
                        "yellow",
                    )
                else:
                    print_colour(
                        f"Deploying a {hub.spec['helm_chart']} from {chart_dir}"
                    )
                if len(hubs) > 1:
                    progress_str = f"{i + 1} / {len(hubs)}: "
                print_colour(
                    f"{progress_str}Validating non-encrypted hub values files for {hub.spec['name']}..."
                )
                validate_hub_config(
                    cluster_name, hub.spec["name"], chart_dir, skip_refresh
                )
                print_colour(
                    f"{progress_str}Validating authenticator config for {hub.spec['name']}..."
                )
                validate_authenticator_config(
                    cluster_name, hub.spec["name"], chart_dir, skip_refresh
                )
                cleanup_values_schema_json(chart_dir)

                print_colour(f"{progress_str}Deploying hub {hub.spec['name']}...")
                hub.deploy(chart_dir, dask_gateway_version, debug, dry_run)
                cleanup_values_schema_json(chart_dir)


async def test_health_attempts(
    hub_url: str,
    service_api_token: str,
    hub_type: str,
    attempts: int,
    attempt_timeout_s: int,
):
    for i in range(attempts):
        try:
            async with asyncio.timeout(attempt_timeout_s):
                await test_hub_healthy(hub_url, service_api_token, hub_type)
        except asyncio.TimeoutError:
            print_colour(f"Attempt {i + 1} timed out, retrying", colour="red")
        except Exception:
            print_colour(
                f"An error occurred during attempt {i + 1}, retrying", colour="red"
            )
        else:
            return

    raise RuntimeError("All attempts failed")


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
def run_hub_health_check(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    attempts: int = typer.Option(
        3, help="Number of failures before declaring unhealthy"
    ),
    attempt_timeout_s: int = typer.Option(
        600, help="Number of seconds before giving up on an attempt"
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
            f"Testing {hub.spec['name']} is not supported yet. Skipping ...",
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

    asyncio.run(
        test_health_attempts(
            hub_url, service_api_token, hub.type, attempts, attempt_timeout_s
        )
    )
