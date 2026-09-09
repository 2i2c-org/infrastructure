import json
import os
from pathlib import Path

import _jsonnet
import hcl2
import typer
from rich.console import Console
from ruamel.yaml import YAML

from deployer.dev.commands.generate.progress_matrix.subchart_version import (
    turn_data_into_table,
)
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    CONFIG_CLUSTERS_PATH,
    REPO_ROOT_PATH,
)

from .progress_matrix_app import progress_matrix_app

yaml = YAML(typ="safe", pure=True)
console = Console()


def build_tfvars_path(cluster_name: str, provider: str) -> Path:
    if cluster_name == "2i2c":
        cluster_name = "pilot-hubs"
    return (
        REPO_ROOT_PATH / "terraform" / provider / "projects" / f"{cluster_name}.tfvars"
    )


def build_eksctl_path(cluster_name: str) -> Path:
    if cluster_name == "nasa-ghg-hub":
        cluster_name = "nasa-ghg"
    return REPO_ROOT_PATH / "eksctl" / f"{cluster_name}.jsonnet"


def load_gcp_k8s_versions(tfvars_path: Path) -> dict[str, str]:
    """Load k8s_versions from a GCP .tfvars file."""
    with tfvars_path.open() as f:
        tfvars = hcl2.load(f)
    return tfvars.get("k8s_versions", {})


def load_aws_k8s_version(jsonnet_path: Path) -> str | None:
    """Extract k8s version from an AWS eksctl jsonnet file."""
    json_text = _jsonnet.evaluate_file(str(jsonnet_path))
    data = json.loads(json_text)
    return data.get("metadata", {}).get("version")


def normalize_gcp_k8s_versions(raw_versions_data: dict[str, str]) -> str:
    """
    Normalize GCP k8s_versions dict to a single string for display.
    - Uses min_master_version as the canonical version.
    - If all other values match it, returns just that version.
    - Otherwise, returns 'min_master_version=version, other_different_version=version2'
    """
    canonical = raw_versions_data.get("min_master_version")

    # Collect different keys or different values than canonical
    others = {k: v for k, v in raw_versions_data.items() if v != canonical}

    if not others:
        # version looks like "1.35.3-gke.1943000" and we want to return 1.35
        # similar to the AWS versioning
        return ".".join(canonical[1:].split(".")[:2])

    parts = [f"min_master_version={canonical}"] + [
        f"{k}={v}" for k, v in others.items()
    ]
    return ", ".join(parts)


def get_k8s_version_for_cluster(cluster_name: str) -> str:
    """
    Get a human-readable k8s version string for a cluster.

    Returns:
      - Version string (possibly normalized)
      - "NOT AVAILABLE" if provider different than GCP and AWS
    """
    cluster = Cluster.from_name(cluster_name)
    with open(cluster.config_dir / "cluster.yaml") as f:
        cluster_config = yaml.load(f)

    provider = cluster_config.get("provider", {})

    if provider == "gcp":
        tfvars_path = build_tfvars_path(cluster_name, provider)
        raw_versions_data = load_gcp_k8s_versions(tfvars_path)
        return normalize_gcp_k8s_versions(raw_versions_data) or "NOT AVAILABLE"
    elif provider == "aws":
        jsonnet_path = build_eksctl_path(cluster_name)
        version = load_aws_k8s_version(jsonnet_path)
        return version or "NOT AVAILABLE"
    else:
        return "NOT AVAILABLE"


@progress_matrix_app.command()
def get_k8s_version(
    cluster_name: str = typer.Argument(None, help="Name of cluster to operate on"),
    threshold: str = typer.Option(
        None,
        help="Versions different than this will be highlighted",
    ),
):
    clusters = os.listdir(CONFIG_CLUSTERS_PATH)
    if cluster_name:
        clusters = [cluster_name]

    k8_versions: dict[str, dict[str, str]] = {}

    for c_name in clusters:
        try:
            cluster = Cluster.from_name(c_name)
            version = get_k8s_version_for_cluster(c_name)

            k8_versions[c_name] = {hub.spec["name"]: version for hub in cluster.hubs}
        except FileNotFoundError:
            continue

    columns = ["Cluster", "Hub", "K8s version"]
    table = turn_data_into_table(
        title="K8s versions",
        columns=columns,
        highlight_idx=2,
        threshold=threshold,
        data=k8_versions,
    )

    console.print(table)
