"""
Functions related to validating configuration files such as helm chart values and our
cluster.yaml files
"""

import functools
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import typer
from ruamel.yaml import YAML

from deployer.cli_app import validate_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
    find_absolute_path_to_cluster_file,
)
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
    rendered during validation or deployment.
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
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

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
    cluster_file = find_absolute_path_to_cluster_file(cluster_name)

    with open(cluster_file) as cf, open(cluster_schema_file) as sf:
        cluster_config = yaml.load(cf)
        schema = yaml.load(sf)
        # Raises useful exception if validation fails
        jsonschema.validate(cluster_config, schema)


@validate_app.command()
def hub_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
):
    """
    Validates the provided non-encrypted helm chart values files for each hub of
    a specific cluster.
    """
    _prepare_helm_charts_dependencies_and_schemas()

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)

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
        for values_file in hub.spec["helm_chart_values_files"]:
            if "secret" not in os.path.basename(values_file):
                cmd.append(f"--values={config_file_path.parent.joinpath(values_file)}")
        # Workaround the current requirement for dask-gateway 0.9.0 to have a
        # JupyterHub api-token specified, for updates if this workaround can be
        # removed, see https://github.com/dask/dask-gateway/issues/473.
        if hub.spec["helm_chart"] == "daskhub":
            cmd.append("--set=dask-gateway.gateway.auth.jupyterhub.apiToken=dummy")
        try:
            subprocess.check_output(cmd, text=True)
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            sys.exit(1)


@validate_app.command()
def support_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
):
    """
    Validates the provided non-encrypted helm chart values files for the support chart
    of a specific cluster.
    """
    _prepare_helm_charts_dependencies_and_schemas()

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    if cluster.support:
        print_colour(
            f"Validating non-encrypted support values files for {cluster_name}..."
        )

        cmd = [
            "helm",
            "template",
            str(HELM_CHARTS_DIR.joinpath("support")),
        ]

        for values_file in cluster.support["helm_chart_values_files"]:
            if "secret" not in os.path.basename(values_file):
                cmd.append(f"--values={config_file_path.parent.joinpath(values_file)}")

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
    For each hub of a specific cluster:
     - It asserts that when the JupyterHub GitHubOAuthenticator is used,
       then `Authenticator.allowed_users` is not set.
       An error is raised otherwise.
    """
    _prepare_helm_charts_dependencies_and_schemas()

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)

    hubs = get_list_of_hubs_to_operate_on(cluster_name, hub_name)

    for i, hub in enumerate(hubs):
        print_colour(
            f"{i+1} / {len(hubs)}: Validating authenticator config for {hub.spec['name']}..."
        )

        authenticator_class = ""
        allowed_users = []
        for values_file_name in hub.spec["helm_chart_values_files"]:
            if "secret" not in os.path.basename(values_file_name):
                values_file = config_file_path.parent.joinpath(values_file_name)
                # Load the hub extra config from its specific values files
                config = yaml.load(values_file)
                # Check if there's config that specifies an authenticator class
                try:
                    if hub.spec["helm_chart"] != "basehub":
                        hub_config = config["basehub"]["jupyterhub"]["hub"]["config"]
                    else:
                        hub_config = config["jupyterhub"]["hub"]["config"]

                    authenticator_class = hub_config["JupyterHub"][
                        "authenticator_class"
                    ]
                    allowed_users = hub_config["Authenticator"]["allowed_users"]
                    org_based_github_auth = False
                    if hub_config.get("GitHubOAuthenticator", None):
                        org_based_github_auth = hub_config["GitHubOAuthenticator"].get(
                            "allowed_organizations", False
                        )
                except KeyError:
                    pass

        # If the authenticator class is github, then raise an error
        # if `Authenticator.allowed_users` is set
        if authenticator_class == "github" and allowed_users and org_based_github_auth:
            raise ValueError(
                f"""
                    Please unset `Authenticator.allowed_users` for {hub.spec['name']} when GitHub Orgs/Teams is
                    being used for auth so valid members are not refused access.
                """
            )


@validate_app.command()
def configurator_config(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
):
    """
    For each hub of a specific cluster:
     - It asserts that when the singleuser configuration overrides the same fields like the configurator, specifically kubespawner_override and profile_options,
       the latter must be disabled.
       An error is raised otherwise.
    """
    _prepare_helm_charts_dependencies_and_schemas()

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)

    hubs = get_list_of_hubs_to_operate_on(cluster_name, hub_name)

    for i, hub in enumerate(hubs):
        print_colour(
            f"{i+1} / {len(hubs)}: Validating configurator and profile lists config for {hub.spec['name']}..."
        )

        configurator_enabled = False
        singleuser_overrides = False
        for values_file_name in hub.spec["helm_chart_values_files"]:
            if "secret" not in os.path.basename(values_file_name):
                values_file = config_file_path.parent.joinpath(values_file_name)
                # Load the hub extra config from its specific values files
                config = yaml.load(values_file)
                try:
                    if hub.spec["helm_chart"] != "basehub":
                        singleuser_config = config["basehub"]["jupyterhub"][
                            "singleuser"
                        ]
                        custom_config = config["basehub"]["jupyterhub"]["custom"]
                    else:
                        singleuser_config = config["jupyterhub"]["singleuser"]
                        custom_config = config["jupyterhub"]["custom"]

                    configurator_enabled = custom_config.get(
                        "jupyterhubConfigurator", {}
                    ).get("enabled")
                    # If it's already disabled we don't have what to check
                    if configurator_enabled:
                        profiles = singleuser_config.get("profileList", None)
                        if profiles:
                            for p in profiles:
                                overrides = p.get("kubespawner_override", None)
                                if overrides and overrides.get("image", None):
                                    singleuser_overrides = True
                                    break
                                options = p.get("profile_options", None)
                                if options and "image" in options:
                                    singleuser_overrides = True
                                    break
                except KeyError:
                    pass

        if configurator_enabled == True and singleuser_overrides == True:
            raise ValueError(
                f"""
                    When the singleuser configuration overrides the same fields like the configurator,
                    the later must be disabled. Please disable the configurator for {hub.spec['name']}.
                """
            )


@validate_app.command()
def all(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(None, help="Name of hub to operate on"),
):
    """
    Validate cluster.yaml and non-encrypted helm config for given hub
    """
    cluster_config(cluster_name)
    support_config(cluster_name)
    hub_config(cluster_name, hub_name)
    authenticator_config(cluster_name, hub_name)
