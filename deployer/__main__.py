"""
Deploy many JupyterHubs to many Kubernetes Clusters
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
from ruamel.yaml import YAML

from auth import KeyProvider
from hub import Cluster
from utils import (
    get_decrypted_file,
    prepare_helm_charts_dependencies_and_schemas,
    print_colour,
    find_absolute_path_to_cluster_file,
)

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)
helm_charts_dir = Path(__file__).parent.parent.joinpath("helm-charts")


def use_cluster_credentials(cluster_name):
    """
    Quickly gain command-line access to a cluster by updating the current
    kubeconfig file to include the deployer's access credentials for the named
    cluster and mark it as the cluster to work against by default.

    This function is to be used with the `use-cluster-credentials` CLI
    command only - it is not used by the rest of the deployer codebase.
    """
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


def deploy_support(cluster_name):
    """
    Deploy support components to a cluster
    """
    validate_cluster_config(cluster_name)

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    if cluster.support:
        with cluster.auth():
            cluster.deploy_support()


def deploy_grafana_dashboards(cluster_name):
    """
    Deploy grafana dashboards to a cluster that provide useful metrics
    for operating a JupyterHub

    Grafana dashboards and deployment mechanism in question are maintained in
    this repo: https://github.com/jupyterhub/grafana-dashboards
    """
    validate_cluster_config(cluster_name)

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


def deploy(cluster_name, hub_name, skip_hub_health_test, config_path):
    """
    Deploy one or more hubs in a given cluster
    """
    validate_cluster_config(cluster_name)
    validate_hub_config(cluster_name, hub_name)

    with get_decrypted_file(config_path) as decrypted_file_path:
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

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    with cluster.auth():
        hubs = cluster.hubs
        if hub_name:
            hub = next((hub for hub in hubs if hub.spec["name"] == hub_name), None)
            hub.deploy(k, SECRET_KEY, skip_hub_health_test)
        else:
            hubN = len(hubs)
            for i, hub in enumerate(hubs):
                print_colour(f"{i+1} / {hubN}: Deploying hub {hub.spec['name']}...")
                hub.deploy(k, SECRET_KEY, skip_hub_health_test)


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
    prepare_helm_charts_dependencies_and_schemas()

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


def main():
    argparser = argparse.ArgumentParser(
        description="""A command line tool to perform various functions related
        to deploying and maintaining a JupyterHub running on kubernetes
        infrastructure
        """
    )
    subparsers = argparser.add_subparsers(
        required=True, dest="action", help="Available subcommands"
    )

    # === Arguments and options shared across subcommands go here ===#
    # NOTE: If we do not add a base_parser here with the add_help=False
    #       option, then we see a "conflicting option strings" error when
    #       running `python deployer --help`
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        "cluster_name",
        type=str,
        help="The name of the cluster to perform actions on",
    )

    # === Add new subcommands in this section ===#
    # Deploy subcommand
    deploy_parser = subparsers.add_parser(
        "deploy",
        parents=[base_parser],
        help="Install/upgrade the helm charts of JupyterHubs on a cluster",
    )
    deploy_parser.add_argument(
        "hub_name",
        nargs="?",
        help="The hub, or list of hubs, to install/upgrade the helm chart for",
    )
    deploy_parser.add_argument(
        "--skip-hub-health-test", action="store_true", help="Bypass the hub health test"
    )
    deploy_parser.add_argument(
        "--config-path",
        help="File to read secret deployment configuration from",
        # This filepath is relative to the PROJECT ROOT
        default="shared/deployer/enc-auth-providers-credentials.secret.yaml",
    )

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        parents=[base_parser],
        help="Validate the cluster.yaml configuration itself, as well as the provided non-encrypted helm chart values files for each hub or the specified hub.",
    )
    validate_parser.add_argument(
        "hub_name",
        nargs="?",
        help="The hub, or list of hubs, to validate provided non-encrypted helm chart values for.",
    )

    # deploy-support subcommand
    deploy_support_parser = subparsers.add_parser(
        "deploy-support",
        parents=[base_parser],
        help="Install/upgrade the support helm release on a given cluster",
    )

    # deploy-grafana-dashboards subcommand
    deploy_grafana_dashboards_parser = subparsers.add_parser(
        "deploy-grafana-dashboards",
        parents=[base_parser],
        help="Deploy grafana dashboards to a cluster for monitoring JupyterHubs. deploy-support must be run first!",
    )

    # use-cluster-credentials subcommand
    use_cluster_credentials_parser = subparsers.add_parser(
        "use-cluster-credentials",
        parents=[base_parser],
        help="Modify the current kubeconfig with the deployer's access credentials for the named cluster",
    )
    # === End section ===#

    args = argparser.parse_args()

    if args.action == "deploy":
        deploy(
            args.cluster_name,
            args.hub_name,
            args.skip_hub_health_test,
            args.config_path,
        )
    elif args.action == "validate":
        validate_cluster_config(args.cluster_name)
        validate_hub_config(args.cluster_name, args.hub_name)
    elif args.action == "deploy-support":
        deploy_support(args.cluster_name)
    elif args.action == "deploy-grafana-dashboards":
        deploy_grafana_dashboards(args.cluster_name)
    elif args.action == "use-cluster-credentials":
        use_cluster_credentials(args.cluster_name)


if __name__ == "__main__":
    main()
