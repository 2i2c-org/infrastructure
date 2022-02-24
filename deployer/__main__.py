"""
Deploy many JupyterHubs to many Kubernetes Clusters
"""
import argparse
import os
import subprocess
from pathlib import Path
import warnings

import jsonschema
from ruamel.yaml import YAML
import shutil

from auth import KeyProvider
from hub import Cluster
from utils import decrypt_file, print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


def use_cluster_credentials(cluster_name):
    """
    Quickly gain command-line access to a cluster by updating the current
    kubeconfig file to include the deployer's access credentials for the named
    cluster and mark it as the cluster to work against by default.

    This function is to be used with the `use-cluster-credentials` CLI
    command only - it is not used by the rest of the deployer codebase.
    """

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    config_file_path = Path(os.getcwd()).joinpath(
        "config", "clusters", cluster_name, "cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

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

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    config_file_path = Path(os.getcwd()).joinpath(
        "config", "clusters", cluster_name, "cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

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

    # Validate our config with JSON Schema first before continuing
    validate(cluster_name)

    config_file_path = Path(os.getcwd()).joinpath(
        "config", "clusters", cluster_name, "cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

    # If grafana support chart is not deployed, then there's nothing to do
    if not cluster.support:
        print_colour(
            "Support chart has not been deployed. Skipping Grafana dashboards deployment..."
        )
        return

    secret_config_file = Path(os.getcwd()).joinpath(
        "secrets", "config", "clusters", f"{cluster_name}.cluster.yaml"
    )

    # Check the secret file exists before continuing
    if not os.path.exists(secret_config_file):
        raise FileExistsError(
            f"File does not exist! Please create it and try again: {secret_config_file}"
        )

    # Read the cluster specific secret config file
    with decrypt_file(secret_config_file) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # Check GRAFANA_TOKEN exists in the secret config file before continuing
    if "grafana_token" not in config.keys():
        raise ValueError(
            f"`grafana_token` not provided in secret file! Please add it and try again: {secret_config_file}"
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

    config_file_path = Path(os.getcwd()).joinpath(
        "config", "clusters", cluster_name, "cluster.yaml"
    )
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f))

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


def validate(cluster_name):
    schema_file = (Path(os.getcwd())).joinpath("shared", "deployer", "cluster.schema.yaml")
    config_file = (Path(os.getcwd())).joinpath("config", "clusters", cluster_name, "cluster.yaml")

    with open(config_file) as cf, open(schema_file) as sf:
        cluster_config = yaml.load(cf)

        if not os.path.dirname(config_file).endswith(cluster_config["name"]):
            warnings.warn(
                "Cluster Name Mismatch: It is convention that the cluster name defined "
                + "in cluster.yaml matches the name of the parent directory. "
                + "Deployment won't be halted but please update this for consistency!"
            )

        schema = yaml.load(sf)
        # Raises useful exception if validation fails
        jsonschema.validate(cluster_config, schema)

    secret_cluster_dir = Path(os.getcwd()).joinpath("secrets", "config", "clusters")
    secret_schema_file = secret_cluster_dir.joinpath("schema.yaml")
    secret_config_file = secret_cluster_dir.joinpath(f"{cluster_name}.cluster.yaml")

    # If a secret config file exists, validate it as well
    if os.path.exists(secret_config_file):
        with decrypt_file(secret_config_file) as decrypted_file_path:
            with open(decrypted_file_path) as scf, open(secret_schema_file) as ssf:
                secret_cluster_config = yaml.load(scf)
                secret_schema = yaml.load(ssf)
                jsonschema.validate(secret_cluster_config, secret_schema)


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
    # NOTE: If you we do not add a base_parser here with the add_help=False
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
        default="shared/deployer/enc-deployer.secret.yaml",
    )

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        parents=[base_parser],
        help="Validate the cluster configuration against a JSON schema",
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
        validate(args.cluster_name)
    elif args.action == "deploy-support":
        deploy_support(args.cluster_name)
    elif args.action == "deploy-grafana-dashboards":
        deploy_grafana_dashboards(args.cluster_name)
    elif args.action == "use-cluster-credentials":
        use_cluster_credentials(args.cluster_name)


if __name__ == "__main__":
    main()
