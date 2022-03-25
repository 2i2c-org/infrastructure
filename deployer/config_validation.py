"""
Functions related to validating configuration files such as helm chart values and our
cluster.yaml files
"""
import functools
import os
import sys
import json
import subprocess
import jsonschema

from pathlib import Path
from ruamel.yaml import YAML

from cluster import Cluster
from utils import print_colour
from file_acquisition import find_absolute_path_to_cluster_file

yaml = YAML(typ="safe", pure=True)
helm_charts_dir = Path(__file__).parent.parent.joinpath("helm-charts")


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
    basehub_dir = helm_charts_dir.joinpath("basehub")
    _generate_values_schema_json(basehub_dir)
    subprocess.check_call(["helm", "dep", "up", basehub_dir])

    daskhub_dir = helm_charts_dir.joinpath("daskhub")
    _generate_values_schema_json(daskhub_dir)
    subprocess.check_call(["helm", "dep", "up", daskhub_dir])

    support_dir = helm_charts_dir.joinpath("support")
    _generate_values_schema_json(support_dir)
    subprocess.check_call(["helm", "dep", "up", support_dir])


def validate_cluster_config(cluster_name):
    """
    Validates cluster.yaml configuration against a JSONSchema.
    """
    cluster_schema_file = Path(os.getcwd()).joinpath(
        "shared", "deployer", "cluster.schema.yaml"
    )
    cluster_file = find_absolute_path_to_cluster_file(cluster_name)

    with open(cluster_file) as cf, open(cluster_schema_file) as sf:
        cluster_config = yaml.load(cf)
        schema = yaml.load(sf)
        # Raises useful exception if validation fails
        jsonschema.validate(cluster_config, schema)


def validate_hub_config(cluster_name, hub_name):
    """
    Validates the provided non-encrypted helm chart values files for each hub of
    a specific cluster.
    """
    _prepare_helm_charts_dependencies_and_schemas()

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    hubs = []
    if hub_name:
        hubs = [h for h in cluster.hubs if h.spec["name"] == hub_name]
    else:
        hubs = cluster.hubs

    for i, hub in enumerate(hubs):
        print_colour(
            f"{i+1} / {len(hubs)}: Validating non-encrypted hub values files for {hub.spec['name']}..."
        )

        cmd = [
            "helm",
            "template",
            str(helm_charts_dir.joinpath(hub.spec["helm_chart"])),
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


def validate_support_config(cluster_name):
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
            str(helm_charts_dir.joinpath("support")),
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
