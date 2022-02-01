"""
Deploy many JupyterHubs to many Kubernetes Clusters
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path

import jsonschema
from ruamel.yaml import YAML
import shutil

from auth import KeyProvider
from hub import Cluster
from utils import decrypt_file, update_authenticator_config, print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


def deploy_support(cluster_name):
    """
    Deploy support components to a cluster
    """

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    config_file_path = (
        Path(os.getcwd()) / "config/clusters" / f"{cluster_name}.cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

    if cluster.support:
        with cluster.auth():
            cluster.deploy_support()


def deploy_jupyterhub_grafana(cluster_name):
    """
    Deploy grafana dashboards for operating a hub
    """

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    config_file_path = (
        Path(os.getcwd()) / "config/clusters" / f"{cluster_name}.cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

    # If grafana support chart is not deployed, then there's nothing to do
    if not cluster.support:
        print_colour(
            "Support chart has not been deployed. Skipping Grafana dashboards deployment..."
        )
        return

    secret_config_file = (
        Path(os.getcwd()) / "secrets/config/clusters" / f"{cluster_name}.cluster.yaml"
    )

    # Read and set GRAFANA_TOKEN from the cluster specific secret config file
    with decrypt_file(secret_config_file) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # Get the url where grafana is running from the cluster config
    grafana_url = (
        cluster.support.get("config", {})
        .get("grafana", {})
        .get("ingress", {})
        .get("hosts", {})
    )
    uses_tls = (
        cluster.support.get("config", {})
        .get("grafana", {})
        .get("ingress", {})
        .get("tls", {})
    )

    if not grafana_url:
        print_colour(
            "Couldn't find `config.grafana.ingress.hosts`. Skipping Grafana dashboards deployment..."
        )
        return

    grafana_url = (
        "https://" + grafana_url[0] if uses_tls else "http://" + grafana_url[0]
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

        print_colour(f"Done! Dasboards deployed to {grafana_url}.")
    finally:
        # Delete the directory where we cloned the repo.
        # The deployer cannot call jsonnet to deploy the dashboards if using a temp directory here.
        # Might be because opening more than once of a temp file is tried
        # (https://docs.python.org/3.8/library/tempfile.html#tempfile.NamedTemporaryFile)
        shutil.rmtree(dashboards_dir)


def deploy(cluster_name, hub_name, skip_hub_health_test, config_path):
    """
    Deploy one or more hubs in a given cluster
    """

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    with decrypt_file(config_path) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # All our hubs use Auth0 for Authentication. This lets us programmatically
    # determine what auth provider each hub uses - GitHub, Google, etc. Without
    # this, we'd have to manually generate credentials for each hub - and we
    # don't want to do that. Auth0 domains are tied to a account, and
    # this is our auth0 domain for the paid account that 2i2c has.
    auth0 = config["auth0"]

    k = KeyProvider(auth0["domain"], auth0["client_id"], auth0["client_secret"])

    # Each hub needs a unique proxy.secretToken. However, we don't want
    # to manually generate & save it. We also don't want it to change with
    # each deploy - that causes a pod restart with downtime. So instead,
    # we generate it based on a single secret key (`PROXY_SECRET_KEY`)
    # combined with the name of each hub. This way, we get unique,
    # cryptographically secure proxy.secretTokens without having to
    # keep much state. We can rotate them by changing `PROXY_SECRET_KEY`.
    # However, if `PROXY_SECRET_KEY` leaks, that means all the hub's
    # proxy.secretTokens have leaked. So let's be careful with that!
    SECRET_KEY = bytes.fromhex(config["secret_key"])

    config_file_path = (
        Path(os.getcwd()) / "config/clusters" / f"{cluster_name}.cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

    with cluster.auth():
        hubs = cluster.hubs
        if hub_name:
            hub = next((hub for hub in hubs if hub.spec["name"] == hub_name), None)
            update_authenticator_config(hub.spec["config"], hub.spec["helm_chart"])
            hub.deploy(k, SECRET_KEY, skip_hub_health_test)
        else:
            for hub in hubs:
                update_authenticator_config(hub.spec["config"], hub.spec["helm_chart"])
                hub.deploy(k, SECRET_KEY, skip_hub_health_test)


def validate(cluster_name):
    cluster_dir = Path(os.getcwd()) / "config/clusters"
    schema_file = cluster_dir / "schema.yaml"
    config_file = cluster_dir / f"{cluster_name}.cluster.yaml"
    with open(config_file) as cf, open(schema_file) as sf:
        cluster_config = yaml.load(cf)
        schema = yaml.load(sf)
        # Raises useful exception if validation fails
        jsonschema.validate(cluster_config, schema)

    secret_cluster_dir = Path(os.getcwd()) / "secrets/config/clusters"
    secret_schema_file = secret_cluster_dir / "schema.yaml"
    secret_config_file = secret_cluster_dir / f"{cluster_name}.cluster.yaml"

    # If a secret config file exists, validate it as well
    if os.path.exists(secret_config_file):
        with decrypt_file(secret_config_file) as decrypted_file_path:
            with open(decrypted_file_path) as scf, open(secret_schema_file) as ssf:
                secret_cluster_config = yaml.load(scf)
                secret_schema = yaml.load(ssf)
                jsonschema.validate(secret_cluster_config, secret_schema)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--config-path",
        help="Read deployment config from this file",
        default="deployment.config.yaml",
    )
    subparsers = argparser.add_subparsers(dest="action")

    deploy_parser = subparsers.add_parser("deploy")
    validate_parser = subparsers.add_parser("validate")
    deploy_support_parser = subparsers.add_parser("deploy-support")
    deploy_grafana_parser = subparsers.add_parser("deploy-grafana")

    deploy_parser.add_argument("cluster_name")
    deploy_parser.add_argument("hub_name", nargs="?")
    deploy_parser.add_argument("--skip-hub-health-test", action="store_true")
    deploy_parser.add_argument(
        "--config-path",
        help="Read deployment config from this file",
        default="config/secrets.yaml",
    )

    validate_parser.add_argument("cluster_name")

    deploy_support_parser.add_argument("cluster_name")

    deploy_grafana_parser.add_argument("cluster_name")

    args = argparser.parse_args()

    if args.action == "deploy":
        deploy(
            args.cluster_name,
            args.hub_name,
            args.skip_hub_health_test,
            args.config_path,
        )
    elif args.action == "validate":
        validate(args.cluster_name)
    elif args.action == "deploy-support":
        deploy_support(args.cluster_name)
    elif args.action == "deploy-grafana":
        deploy_jupyterhub_grafana(args.cluster_name)
    else:
        # Print help message and exit when no arguments are passed
        # FIXME: Is there a better way to do this?
        print(argparser.format_help(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
