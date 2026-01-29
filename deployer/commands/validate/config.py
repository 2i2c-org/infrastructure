"""
Functions related to validating configuration files such as helm chart values and our
cluster.yaml files
"""

import functools
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import ExitStack, contextmanager
from pathlib import Path

import jsonschema
import typer
from ruamel.yaml import YAML

from deployer.cli_app import validate_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
    REPO_ROOT_PATH,
)
from deployer.utils.jsonnet import render_jsonnet
from deployer.utils.rendering import print_colour

yaml = YAML(typ="safe", pure=True)

CUSTOM_HUB_CHART_PREFIX = "2i2c-custom-hub-chart"


@functools.lru_cache
def _generate_values_schema_json(helm_chart_dir):
    """
    This function reads the values.schema.yaml files part of our Helm charts and
    generates a values.schema.json that can allowing helm the CLI to perform
    validation of passed values before rendering templates or making changes in k8s.
    """
    values_schema_yaml = os.path.join(helm_chart_dir, "values.schema.yaml")
    values_schema_json = os.path.join(helm_chart_dir, "values.schema.json")

    with open(values_schema_yaml) as f:
        schema = yaml.load(f)
    with open(values_schema_json, "w") as f:
        json.dump(schema, f)


def cleanup_values_schema_json(helm_chart_dir):
    values_schema_json = os.path.join(helm_chart_dir, "values.schema.json")
    if os.path.exists(values_schema_json):
        os.remove(values_schema_json)


@functools.lru_cache
def _prepare_support_helm_charts_dependencies_and_schema():
    support_dir = HELM_CHARTS_DIR.joinpath("support")
    _generate_values_schema_json(support_dir)
    subprocess.check_call(["helm", "dep", "up", support_dir])


@functools.lru_cache
def _prepare_hub_helm_charts_dependencies_and_schema(hub_chart_dir, legacy_daskub):
    # FIXME: replace all string paths with Path objects
    hub_chart_dir = Path(hub_chart_dir)
    cleanup_values_schema_json(hub_chart_dir)

    if legacy_daskub:
        if not hub_chart_dir.name.startswith(CUSTOM_HUB_CHART_PREFIX):
            _generate_values_schema_json(HELM_CHARTS_DIR / "basehub")
            subprocess.check_call(["helm", "dep", "up", HELM_CHARTS_DIR / "basehub"])
    else:
        _generate_values_schema_json(hub_chart_dir)

    subprocess.check_call(["helm", "dep", "up", hub_chart_dir])


def validate_hub_config(
    cluster_name,
    hub_name,
    helm_chart_dir="",
    skip_refresh=False,
    debug=False,
):
    """
    Validates the provided non-encrypted helm chart values files for each hub of
    a specific cluster.
    """
    cluster = Cluster.from_name(cluster_name)
    hub = next((h for h in cluster.hubs if h.spec["name"] == hub_name), None)

    if not helm_chart_dir:
        helm_chart_dir = HELM_CHARTS_DIR / hub.spec["helm_chart"]
    if not skip_refresh:
        _prepare_hub_helm_charts_dependencies_and_schema(
            helm_chart_dir, hub.legacy_daskhub
        )

    cmd = [
        "helm",
        "template",
        helm_chart_dir,
    ]
    if debug:
        cmd.append("--debug")

    with ExitStack() as jsonnet_stack:
        for values_file in hub.spec["helm_chart_values_files"]:
            # FIXME: The logic here for figuring out non secret files is not correct
            if values_file.endswith(".jsonnet"):
                rendered_file = jsonnet_stack.enter_context(
                    render_jsonnet(
                        cluster.config_dir / values_file,
                        cluster_name,
                        hub_name,
                        cluster.spec["provider"],
                    )
                )
                cmd.append(f"--values={rendered_file}")
            elif "secret" not in os.path.basename(values_file):
                values_file = cluster.config_dir / values_file
                cmd.append(f"--values={values_file}")
                config = yaml.load(values_file)
                # Check if there's config that enables dask-gateway
                dask_gateway_enabled = config.get("dask-gateway", {}).get(
                    "enabled", False
                )

        # Workaround the current requirement for dask-gateway 0.9.0 to have a
        # JupyterHub api-token specified, for updates if this workaround can be
        # removed, see https://github.com/dask/dask-gateway/issues/473.
        if dask_gateway_enabled:
            cmd.append("--set=dask-gateway.gateway.auth.jupyterhub.apiToken=dummy")
        try:
            subprocess.check_output(cmd, text=True)
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            sys.exit(1)


@contextmanager
def get_chart_dir(default_chart_dir, chart_override, chart_override_path):
    """
    Returns the default chart directory (basehub or daskhub)
    or a temporary directory.

    The temporary directory is holding a copy of the contents of the
    helm-charts/basehub dir where Chart.yaml is overridden by whichever yaml
    file was passed in the cluster's `cluster.yaml` file under `chart_override`
    """
    chart_dir = default_chart_dir
    try:
        if chart_override:
            # if we're overriding the Chart.yaml file, then we need to make sure
            # that we're copying the contents for helm-charts/basehub and not the
            # deprecated daskhub chart
            default_chart_dir = HELM_CHARTS_DIR / "basehub"
            temp_chart_dir = tempfile.TemporaryDirectory(prefix=CUSTOM_HUB_CHART_PREFIX)
            temp_chart_dir_name = temp_chart_dir.name
            # copy the chart directory into the temporary location
            shutil.copytree(default_chart_dir, temp_chart_dir_name, dirs_exist_ok=True)
            # copy the chart override file into the temporary chart directory
            shutil.copy(chart_override_path, temp_chart_dir_name)
            # rename the override file so that it overrides "Chart.yaml"
            default_chart_yaml = Path(temp_chart_dir_name) / "Chart.yaml"
            os.rename(Path(temp_chart_dir_name) / chart_override, default_chart_yaml)
            chart_dir = Path(temp_chart_dir_name)
        yield chart_dir
    finally:
        if chart_override:
            temp_chart_dir.cleanup()


def validate_authenticator_config(
    cluster_name,
    hub_name,
    helm_chart_dir,
    skip_refresh=False,
):
    """
    For each hub of a specific cluster it asserts that:
    - when the JupyterHub GitHubOAuthenticator is used, then allowed_users is not set
    - when the dummy authenticator is used, then admin_users is the empty list
    """

    cluster = Cluster.from_name(cluster_name)
    hub = next((h for h in cluster.hubs if h.spec["name"] == hub_name), None)

    if not skip_refresh:
        _prepare_hub_helm_charts_dependencies_and_schema(
            helm_chart_dir, hub.legacy_daskhub
        )

    allowed_users = []
    admin_users = "Jargon-Chlorine7-Undergo"
    for values_file_name in hub.spec["helm_chart_values_files"]:
        if "secret" not in os.path.basename(values_file_name):
            values_file = cluster.config_dir / values_file_name
            # Load the hub extra config from its specific values files
            config = yaml.load(values_file)
            # Check if there's config that specifies an authenticator class
            try:
                # This special casing is needed for legacy daskhubs still
                # using the daskhub chart
                if hub.legacy_daskhub:
                    config = config.get("basehub", {})
                hub_config = (
                    config.get("jupyterhub", {}).get("hub", {}).get("config", {})
                )
                allowed_users = hub_config.get("Authenticator", {}).get("allowed_users")
                admin_users = hub_config.get("Authenticator", {}).get("admin_users")
                org_based_github_auth = False
                if hub_config.get("GitHubOAuthenticator", None):
                    org_based_github_auth = hub_config["GitHubOAuthenticator"].get(
                        "allowed_organizations", False
                    )
            except KeyError:
                pass
    # If the authenticator class is github, then raise an error
    # if `Authenticator.allowed_users` is set
    if hub.authenticator == "github" and allowed_users and org_based_github_auth:
        raise ValueError(
            f"""
                Please unset `Authenticator.allowed_users` for {hub.spec["name"]} when GitHub Orgs/Teams is
                being used for auth so valid members are not refused access.
            """
        )
    elif hub.authenticator == "dummy" and admin_users != []:
        raise ValueError(
            f"""
                For security reasons, please unset `Authenticator.admin_users` for {hub.spec["name"]} when the dummy authenticator is
                being used for authentication.
            """
        )


@validate_app.command()
def support_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    debug: bool = typer.Option(False, help="Enable verbose output"),
    skip_refresh: bool = typer.Option(
        False,
        help="Skip the helm dep update",
    ),
):
    """
    Validates the provided non-encrypted helm chart values files for the support chart
    of a specific cluster.
    """
    if not skip_refresh:
        _prepare_support_helm_charts_dependencies_and_schema()

    cluster = Cluster.from_name(cluster_name)

    if cluster.support:
        print_colour(
            f"Validating non-encrypted support values files for {cluster_name}..."
        )

        cmd = [
            "helm",
            "template",
            str(HELM_CHARTS_DIR.joinpath("support")),
        ]
        if debug:
            cmd.append("--debug")

        with ExitStack() as jsonnet_stack:
            for values_file in cluster.support["helm_chart_values_files"]:
                if values_file.endswith(".jsonnet"):
                    rendered_file = jsonnet_stack.enter_context(
                        render_jsonnet(
                            cluster.config_dir / values_file,
                            cluster_name,
                            None,
                            cluster.spec["provider"],
                        )
                    )
                    cmd.append(f"--values={rendered_file}")
                # FIXME: The logic here for figuring out non secret files is not correct
                elif "secret" not in os.path.basename(values_file):
                    cmd.append(f"--values={cluster.config_dir / values_file}")
            try:
                subprocess.check_output(cmd, text=True)
            except subprocess.CalledProcessError as e:
                print(e.stdout)
                sys.exit(1)
    else:
        print_colour(f"No support defined for {cluster_name}. Nothing to validate!")


@validate_app.command()
def cluster_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
):
    """
    Validates cluster.yaml configuration against a JSONSchema.
    """
    cur_dir = Path(__file__).parent
    cluster_schema_file = cur_dir.joinpath("cluster.schema.yaml")

    cluster = Cluster.from_name(cluster_name)

    with open(cluster_schema_file) as sf:
        schema = yaml.load(sf)
        try:
            jsonschema.validate(cluster.spec, schema)
        except jsonschema.ValidationError as e:
            print_colour(
                f"JSON schema validation error in cluster.yaml for {cluster_name}: {e.message}",
                colour="red",
            )
            sys.exit(1)


@validate_app.command()
def all_hub_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
    skip_refresh: bool = typer.Option(False, help="Skip the helm dep update"),
    debug: bool = typer.Option(False, help="Enable verbose output"),
):
    """
    Validates the provided non-encrypted helm chart values files and the
    authenticator configuration for each hub of a specific cluster.
    """
    cluster = Cluster.from_name(cluster_name)
    if hub_name:
        hubs = [h for h in cluster.hubs if h.spec["name"] == hub_name]
    else:
        hubs = cluster.hubs
    for i, hub in enumerate(hubs):
        default_chart_dir = HELM_CHARTS_DIR / hub.spec["helm_chart"]
        chart_override = hub.spec.get("chart_override", None)
        if chart_override and "/" in chart_override:
            chart_override_path = REPO_ROOT_PATH / chart_override
            chart_override = chart_override.split("/")[-1]
        else:
            chart_override_path = (
                hub.cluster.config_dir / chart_override if chart_override else None
            )
        with get_chart_dir(
            default_chart_dir, chart_override, chart_override_path
        ) as chart_dir:
            print_colour(
                f"{i + 1} / {len(hubs)}: Validating hub and authenticator config for {hub.spec['name']}..."
            )
            validate_hub_config(
                cluster_name,
                hub.spec["name"],
                helm_chart_dir=chart_dir,
                skip_refresh=skip_refresh,
                debug=debug,
            )
            validate_authenticator_config(
                cluster_name, hub.spec["name"], chart_dir, skip_refresh
            )
            cleanup_values_schema_json(chart_dir)
