"""
Functions related to validating configuration files such as helm chart values and our
cluster.yaml files
"""

import functools
import json
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path

import jsonschema
import typer
from ruamel.yaml import YAML

from deployer.cli_app import validate_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
)
from deployer.utils.jsonnet import render_jsonnet
from deployer.utils.rendering import print_colour

yaml = YAML(typ="safe", pure=True)


@functools.lru_cache
def _generate_values_schema_json(helm_chart_dir):
    """
    This script reads the values.schema.yaml files part of our Helm charts and
    generates a values.schema.json that can allowing helm the CLI to perform
    validation of passed values before rendering templates or making changes in k8s.

    FIXME: Currently we have a hard coupling between the deployer script and the
           Helm charts part of this repo. Managing the this logic here is a
           compromise but it should really be managed as part of packaging it
           and uploading it to a helm chart registry instead.
    """
    values_schema_yaml = os.path.join(helm_chart_dir, "values.schema.yaml")
    values_schema_json = os.path.join(helm_chart_dir, "values.schema.json")

    with open(values_schema_yaml) as f:
        schema = yaml.load(f)
    with open(values_schema_json, "w") as f:
        json.dump(schema, f)


@functools.lru_cache
def _prepare_helm_charts_dependencies_and_schemas():
    """
    Ensures that the helm charts we deploy, basehub and daskhub, have got their
    dependencies updated and .json schema files generated so that they can be
    """
    basehub_dir = HELM_CHARTS_DIR.joinpath("basehub")
    _generate_values_schema_json(basehub_dir)
    subprocess.check_call(["helm", "dep", "up", basehub_dir])

    daskhub_dir = HELM_CHARTS_DIR.joinpath("daskhub")
    # Not generating schema for daskhub, as it is dead
    subprocess.check_call(["helm", "dep", "up", daskhub_dir])

    support_dir = HELM_CHARTS_DIR.joinpath("support")
    _generate_values_schema_json(support_dir)
    subprocess.check_call(["helm", "dep", "up", support_dir])


def get_list_of_hubs_to_operate_on(cluster_name, hub_name):
    cluster = Cluster.from_name(cluster_name)

    if hub_name:
        return [h for h in cluster.hubs if h.spec["name"] == hub_name]

    return cluster.hubs


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
def hub_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
    skip_refresh: bool = typer.Option(
        False, "--skip-refresh", help="Skip the helm dep update"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable verbose output"),
):
    """
    Validates the provided non-encrypted helm chart values files for each hub of
    a specific cluster.
    """
    if not skip_refresh:
        _prepare_helm_charts_dependencies_and_schemas()

    cluster = Cluster.from_name(cluster_name)

    hubs = get_list_of_hubs_to_operate_on(cluster_name, hub_name)

    for i, hub in enumerate(hubs):
        print_colour(
            f"{i+1} / {len(hubs)}: Validating non-encrypted hub values files for {hub.spec['name']}..."
        )

        cmd = [
            "helm",
            "template",
            str(HELM_CHARTS_DIR.joinpath(hub.spec["helm_chart"])),
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


@validate_app.command()
def support_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    debug: bool = typer.Option(False, "--debug", help="Enable verbose output"),
):
    """
    Validates the provided non-encrypted helm chart values files for the support chart
    of a specific cluster.
    """
    _prepare_helm_charts_dependencies_and_schemas()

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
                            cluster.config_dir / values_file, cluster_name, None
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
def authenticator_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
):
    """
    For each hub of a specific cluster it asserts that:
    - when the JupyterHub GitHubOAuthenticator is used, then allowed_users is not set
    - when the dummy authenticator is used, then admin_users is the empty list
    """
    _prepare_helm_charts_dependencies_and_schemas()

    cluster = Cluster.from_name(cluster_name)

    hubs = get_list_of_hubs_to_operate_on(cluster_name, hub_name)

    for i, hub in enumerate(hubs):
        print_colour(
            f"{i+1} / {len(hubs)}: Validating authenticator config for {hub.spec['name']}..."
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
                    allowed_users = hub_config.get("Authenticator", {}).get(
                        "allowed_users"
                    )
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
                    Please unset `Authenticator.allowed_users` for {hub.spec['name']} when GitHub Orgs/Teams is
                    being used for auth so valid members are not refused access.
                """
            )
        elif hub.authenticator == "dummy" and admin_users != []:
            raise ValueError(
                f"""
                    For security reasons, please unset `Authenticator.admin_users` for {hub.spec['name']} when the dummy authenticator is
                    being used for authentication.
                """
            )


@validate_app.command()
def all(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
    skip_refresh: bool = typer.Option(
        False, "--skip-refresh", help="Skip the helm dep update"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable verbose output"),
):
    """
    Validate cluster.yaml and non-encrypted helm config for given hub
    """
    cluster_config(cluster_name)
    support_config(cluster_name, debug=debug)
    hub_config(cluster_name, hub_name, skip_refresh=skip_refresh, debug=debug)
    authenticator_config(cluster_name, hub_name)
