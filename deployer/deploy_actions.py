"""
Actions available when deploying many JupyterHubs to many Kubernetes clusters
"""
import os
import shutil
import subprocess
from pathlib import Path

from ruamel.yaml import YAML

from auth import Auth0ClientProvider
from cilogon_auth import CILogonClientProvider
from cluster import Cluster
from utils import print_colour
from file_acquisition import find_absolute_path_to_cluster_file, get_decrypted_file
from config_validation import (
    validate_cluster_config,
    validate_hub_config,
    validate_support_config,
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
    validate_support_config(cluster_name)

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


def deploy(cluster_name, hub_name, skip_hub_health_test, config_path):
    """
    Deploy one or more hubs in a given cluster
    """
    validate_cluster_config(cluster_name)
    validate_hub_config(cluster_name, hub_name)

    with get_decrypted_file(config_path) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    # Some of our hubs use Auth0 for Authentication and some use CILogong.
    # This lets us programmatically determine what auth provider each hub
    # uses - GitHub, Google, etc or which Institutional Identity Provider.
    # Without this, we'd have to manually generate credentials for each
    # hub - and we don't want to do that. Auth0 domains are tied to a account,
    # and this is our auth0 domain for the paid account that 2i2c has.
    auth0 = config["auth0"]
    cilogon_admin = config["cilogon_admin"]

    def _get_client_provider(hub_config):
        if hub_config["auth0"].get("enabled", True):
            return Auth0ClientProvider(
                auth0["client_id"], auth0["client_secret"], auth0["domain"]
            )

        return CILogonClientProvider(
            cilogon_admin["client_id"], cilogon_admin["client_secret"]
        )

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
            client_provider = _get_client_provider(hub.spec)
            print_colour(f"Deploying hub {hub.spec['name']}...")
            hub.deploy(client_provider, SECRET_KEY, skip_hub_health_test)
        else:
            for i, hub in enumerate(hubs):
                print_colour(
                    f"{i+1} / {len(hubs)}: Deploying hub {hub.spec['name']}..."
                )
                client_provider = _get_client_provider(hub.spec)
                hub.deploy(client_provider, SECRET_KEY, skip_hub_health_test)
