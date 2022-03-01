import os
import json
import tempfile
import subprocess
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from contextlib import contextmanager, ExitStack
from pathlib import Path
import warnings

yaml = YAML(typ="safe", pure=True)


def assert_file_exists(filepath):
    """Assert a filepath exists, raise an error if not. This function is to be used for
    files that *absolutely have to exist* in order to successfully complete deployment,
    such as, files listed in the `helm_chart_values_file` key in the `cluster.yaml` file

    Args:
        filepath (str): Absolute path to the file that is to be asserted for existence
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"""
            File Not Found at following location! Have you checked it's the correct path?
            {filepath}
        """
        )


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
def verify_and_decrypt_file(encrypted_path):
    """
    Provide secure, temporarily decrypted contents of a given file. We verify the file
    is sops-encrypted and raise an error if we do not find the sops key when we expect
    to, in case the decrypted contents have been leaked via version control.

    Args:
        encrypted_path (path object): Absolute path to an encrypted file to perform
            checks on and decrypt

    Yields:
        decrypted_path (path object): Abolute path to a tempfile containing the
            decrypted contents. Unless the file is not valid JSON/YAML or does not have
            the prefix `enc-`, then we return the original, encrypted path.
    """
    assert_file_exists(encrypted_path)
    filename = os.path.basename(encrypted_path)
    _, ext = os.path.splitext(filename)

    # Our convention is that encrypted secrets in the repository begin with "enc-",
    # so first we check for that
    if filename.startswith("enc-"):
        # We must then determine if the file is using sops
        # sops files are JSON/YAML with a `sops` key. So we first check
        # if the file is valid JSON/YAML, and then if it has a `sops` key
        with open(encrypted_path) as f:

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
            raise KeyError(
                "Expecting to find the `sops` key in this encrypted file - but it "
                + "wasn't found! Please regenerate the secret in case it has been "
                + "checked into version control and leaked!"
            )

        # If file has a `sops` key, we assume it's sops encrypted
        with tempfile.NamedTemporaryFile() as f:
            subprocess.check_call(
                ["sops", "--output", f.name, "--decrypt", encrypted_path]
            )
            yield f.name

    else:
        # Hmmm. A file has been passed to this function but does not have the `enc-`
        # prefix. What is the correct thing to do here? For now, we do what has been
        # done before and return the path to the encrypted file
        yield encrypted_path
        return


@contextmanager
def get_decrypted_files(files, abspath):
    """
    This is a context manager that when entered provides a list of
    file paths, where temporary files have been created if needed for
    files that were encrypted and first need to be decrypted.
    """
    with ExitStack() as stack:
        yield [
            stack.enter_context(verify_and_decrypt_file(abspath.joinpath(f)))
            for f in files
            if assert_file_exists(abspath.joinpath(f))  # Check the file exists
        ]


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
