import os
import json
import tempfile
import subprocess
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from contextlib import contextmanager
from pathlib import Path
import warnings

yaml = YAML(typ="safe", pure=True)


def find_absolute_path_to_cluster_file(cluster_name: str):
    """Find the absolute path to a cluster.yaml file for a named cluster

    Args:
        cluster_name (str): The name of the cluster we wish to perform actions on.
            This corresponds to a folder name, and that folder should contain a
            cluster.yaml file.

    Returns:
        Path object: The absolute path to the cluster.yaml file for the named cluster
    """
    filepaths = list((Path(os.getcwd())).glob(f"**/{cluster_name}/cluster.yaml"))

    if len(filepaths) > 1:
        raise FileExistsError(
            "Multiple files found. "
            + "Only ONE (1) cluster.yaml file should exist per cluster folder."
        )
    elif len(filepaths) == 0:
        raise FileNotFoundError(
            f"No cluster.yaml file exists for cluster {cluster_name}. "
            + "Please create one and then continue."
        )
    else:
        cluster_file = filepaths[0]

    with open(cluster_file) as cf:
        cluster_config = yaml.load(cf)

    if not os.path.dirname(cluster_file).endswith(cluster_config["name"]):
        warnings.warn(
            "Cluster Name Mismatch: It is convention that the cluster name defined "
            + "in cluster.yaml matches the name of the parent directory. "
            + "Deployment won't be halted but please update this for consistency!"
        )

    return cluster_file


@contextmanager
def decrypt_file(encrypted_path):
    """
    Provide secure temporary decrypted contents of a given file

    If file isn't a sops encrypted file, we assume no encryption is used
    and return the current path.
    """
    # We must first determine if the file is using sops
    # sops files are JSON/YAML with a `sops` key. So we first check
    # if the file is valid JSON/YAML, and then if it has a `sops` key
    with open(encrypted_path) as f:
        _, ext = os.path.splitext(encrypted_path)
        # Support the (clearly wrong) people who use .yml instead of .yaml
        if ext == ".yaml" or ext == ".yml":
            try:
                encrypted_data = yaml.load(f)
            except ScannerError:
                yield encrypted_path
                return
        elif ext == ".json":
            try:
                encrypted_data = json.load(f)
            except json.JSONDecodeError:
                yield encrypted_path
                return

    if "sops" not in encrypted_data:
        yield encrypted_path
        return

    # If file has a `sops` key, we assume it's sops encrypted
    with tempfile.NamedTemporaryFile() as f:
        subprocess.check_call(["sops", "--output", f.name, "--decrypt", encrypted_path])
        yield f.name


def print_colour(msg: str):
    """Print messages in colour to be distinguishable in CI logs

    See the mybinder.org deploy.py script for more details:
    https://github.com/jupyterhub/mybinder.org-deploy/blob/master/deploy.py

    Args:
        msg (str): The message to print in colour
    """
    if os.environ.get("TERM"):
        BOLD = subprocess.check_output(["tput", "bold"]).decode()
        GREEN = subprocess.check_output(["tput", "setaf", "2"]).decode()
        NC = subprocess.check_output(["tput", "sgr0"]).decode()
    else:
        # no term, no colors
        BOLD = GREEN = NC = ""

    print(BOLD + GREEN + msg + NC, flush=True)
