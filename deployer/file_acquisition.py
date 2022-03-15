"""
Functions related to finding and reading files. Checking files exist, finding their
absolute paths, decrypting and reading encrypted files when needed.
"""
import os
import json
import warnings
import subprocess
import tempfile

from pathlib import Path
from contextlib import contextmanager, ExitStack

from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

yaml = YAML(typ="safe", pure=True)


def _assert_file_exists(filepath):
    """Assert a filepath exists, raise an error if not. This function is to be used for
    files that *absolutely have to exist* in order to successfully complete deployment,
    such as, files listed in the `helm_chart_values_file` key in the `cluster.yaml` file

    Args:
        filepath (str): Absolute path to the file that is to be asserted for existence
    """
    if not os.path.isfile(filepath):
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
def get_decrypted_file(original_filepath):
    """
    Assert that a given file exists. If the file is sops-encryped, we provide secure,
    temporarily decrypted contents of the file. We raise an error if we do not find the
    sops key when we expect to, in case the decrypted contents have been leaked via
    version control. We expect to find the sops key in a file if the filename begins
    with "enc-" or contains the word "secret". If the file is not encrypted, we return
    the original filepath.

    Args:
        original_filepath (path object): Absolute path to a file to perform checks on
            and decrypt if it's encrypted

    Yields:
        (path object): EITHER the absolute path to a tempfile containing the
            decrypted contents, OR the original filepath. The original filepath is
            yielded if the file is not valid JSON/YAML, or does not have the prefix
            'enc-' or contain 'secret'.
    """
    _assert_file_exists(original_filepath)
    filename = os.path.basename(original_filepath)
    _, ext = os.path.splitext(filename)

    # Our convention is that encrypted secrets in the repository begin with "enc-" and include
    # "secret" in the filename, so first we check for that. We use an 'or' conditional here since
    # we want to catch files that contain "secret" but do not have the "enc-" prefix and ensure
    # they are encrypted, raising an error if not.
    if filename.startswith("enc-") or ("secret" in filename):
        # We must then determine if the file is using sops
        # sops files are JSON/YAML with a `sops` key. So we first check
        # if the file is valid JSON/YAML, and then if it has a `sops` key.
        # Since valid JSON is also valid YAML by design, a YAML parser can read in JSON.
        with open(original_filepath) as f:
            try:
                content = yaml.load(f)
            except ScannerError:
                yield original_filepath
                return

        if "sops" not in content:
            raise KeyError(
                "Expecting to find the `sops` key in this encrypted file - but it "
                + "wasn't found! Please regenerate the secret in case it has been "
                + "checked into version control and leaked!"
            )

        # If file has a `sops` key, we assume it's sops encrypted
        with tempfile.NamedTemporaryFile() as f:
            subprocess.check_call(
                ["sops", "--output", f.name, "--decrypt", original_filepath]
            )
            yield f.name

    else:
        # For a file that does not match our naming conventions for secrets, yield the
        # original path
        yield original_filepath


@contextmanager
def get_decrypted_files(files, abspath):
    """
    This is a context manager that combines multiple `get_decrypted_file`
    context managers that open and/or decrypt the files in `files`.
    """
    with ExitStack() as stack:
        yield [
            stack.enter_context(get_decrypted_file(abspath.joinpath(f))) for f in files
        ]
