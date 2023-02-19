import os
import subprocess
from pathlib import Path

from ruamel.yaml import YAML

from ..file_acquisition import find_absolute_path_to_cluster_file, get_decrypted_file

yaml = YAML(typ="safe")


def get_grafana_url(cluster_name):
    """
    Return a Grafana instance URL using the cluster's "support.values.yaml"
    file's grafana.ingress.tls[0].hosts[0] config.
    """
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent

    config_file = cluster_config_dir_path.joinpath("support.values.yaml")
    with open(config_file) as f:
        support_config = yaml.load(f)

    grafana_tls_config = (
        support_config.get("grafana", {}).get("ingress", {}).get("tls", [])
    )
    if not grafana_tls_config:
        raise ValueError(f"grafana.ingress.tls config for {cluster_name} missing!")

    # We only have one tls host right now. Modify this when things change.
    return "https://" + grafana_tls_config[0]["hosts"][0]


def get_cluster_prometheus_address(cluster_name):
    """
    Retrieve the address of the prometheus instance running on the `cluster_name` cluster.
    This address is stored in the `support.values.yaml` file of each cluster config directory.

    Args:
        cluster_name: name of the cluster
    Returns:
        string object: https address of the prometheus instance
    Raises ValueError if:
        - `prometheusIngressAuthSecret` isn't configured
        - `support["prometheus"]["server"]["ingress"]["tls"]` doesn't exist
    """
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent

    config_file = cluster_config_dir_path.joinpath("support.values.yaml")
    with open(config_file) as f:
        support_config = yaml.load(f)

    # Don't return the address if the prometheus instance wasn't securely exposed to the outside.
    if not support_config.get("prometheusIngressAuthSecret", {}).get("enabled", False):
        raise ValueError(
            f"`prometheusIngressAuthSecret` wasn't configured for {cluster_name}"
        )

    tls_config = (
        support_config.get("prometheus", {})
        .get("server", {})
        .get("ingress", {})
        .get("tls", [])
    )

    if not tls_config:
        raise ValueError(
            f"No tls config was found for the prometheus instance of {cluster_name}"
        )

    # We only have one tls host right now. Modify this when things change.
    return tls_config[0]["hosts"][0]


def get_cluster_prometheus_creds(cluster_name):
    """
    Retrieve the credentials of the prometheus instance running on the `cluster_name` cluster.
    These credentials are stored in `enc-support.secret.values.yaml` file of each cluster config directory.

    Args:
        cluster_name: name of the cluster
    Returns:
        dict object: {username: `username`, password: `password`}
    """
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent

    config_filename = cluster_config_dir_path.joinpath("enc-support.secret.values.yaml")

    with get_decrypted_file(config_filename) as decrypted_path:
        with open(decrypted_path) as f:
            prometheus_config = yaml.load(f)

    return prometheus_config.get("prometheusIngressAuthSecret", {})


def get_grafana_admin_password():
    """
    Retrieve the password of the grafana `admin` user
    stored in "helm-charts/support/enc-support.secret.values.yaml"

    Returns:
        string object: password of the admin user
    """
    repo_root = Path(__file__).parent.parent.parent

    grafana_credentials_filename = repo_root.joinpath(
        "helm-charts/support/enc-support.secret.values.yaml"
    )

    with get_decrypted_file(grafana_credentials_filename) as decrypted_path:
        with open(decrypted_path) as f:
            grafana_creds = yaml.load(f)

    return grafana_creds.get("grafana", {}).get("adminPassword", None)


def get_grafana_token(cluster_name):
    """
    Get the access token stored in the `enc-grafana-token.secret.yaml` file for
    the <cluster_name>'s Grafana.

    This access token should have enough permissions to create datasources.

    Returns:
        token: the grafana_token stored in the `enc-grafana-token.secret.yaml` file
    """
    # Get the location of the file that stores the central grafana token
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent

    grafana_token_file = cluster_config_dir_path.joinpath(
        "enc-grafana-token.secret.yaml"
    )

    # Read the secret grafana token file
    with get_decrypted_file(grafana_token_file) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)
    if "grafana_token" not in config.keys():
        raise ValueError(
            f"Grafana service account token not found, use `deployer new-grafana-token {cluster_name}`"
        )

    return config["grafana_token"]


def update_central_grafana_token(cluster_name, token):
    """
    Update the API token stored in the `enc-grafana-token.secret.yaml` file
    for the <cluster_name>'s Grafana.
    This access token should have enough permissions to create datasources.

    - If the file `enc-grafana-token.secret.yaml` doesn't exist, it creates one and
      writes the `token` under `grafana_token` key.
    - If the file `enc-grafana-token.secret.yaml` already exists, it updates the token in it by
      first deleting the file and then creating a new (encrypted) one
      where it writes the `token` under `grafana_token` key.
    """
    # Get the location of the file that stores the central grafana token
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent

    grafana_token_file = (cluster_config_dir_path).joinpath(
        "enc-grafana-token.secret.yaml"
    )

    # If grafana token file exists delete it and then create it again with new token
    # Fastest way to update the token
    if os.path.exists(grafana_token_file):
        os.remove(grafana_token_file)

    with open(grafana_token_file, "w") as f:
        f.write(f"grafana_token: {token}")

    # Encrypt the private key
    subprocess.check_call(["sops", "--in-place", "--encrypt", grafana_token_file])
