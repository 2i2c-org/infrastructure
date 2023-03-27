"""
Functions related to finding and reading files. Checking files exist, finding their
absolute paths, decrypting and reading encrypted files when needed.
"""
import json
import os
import subprocess
import tempfile
import warnings
from contextlib import ExitStack, contextmanager
from pathlib import Path

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


def find_absolute_path_to_cluster_file(cluster_name: str, is_test: bool = False):
    """Find the absolute path to a cluster.yaml file for a named cluster

    Args:
        cluster_name (str): The name of the cluster we wish to perform actions on.
            This corresponds to a folder name, and that folder should contain a
            cluster.yaml file.

    Returns:
        Path object: The absolute path to the cluster.yaml file for the named cluster
    """
    root_dir = Path(__file__).parent.parent
    cluster_yaml_path = root_dir.joinpath(
        f"config/clusters/{cluster_name}/cluster.yaml"
    )

    if not cluster_yaml_path.exists():
        raise FileNotFoundError(
            f"No cluster.yaml file exists for cluster {cluster_name}. "
            + "Please create one and then continue."
        )

    with open(cluster_yaml_path) as cf:
        cluster_config = yaml.load(cf)

    if cluster_yaml_path.parent.name != cluster_config["name"]:
        warnings.warn(
            "Cluster Name Mismatch: It is convention that the cluster name defined "
            + "in cluster.yaml matches the name of the parent directory. "
            + "Deployment won't be halted but please update this for consistency!"
        )

    return cluster_yaml_path


def build_absolute_path_to_hub_encrypted_config_file(cluster_name, hub_name):
    """Builds the absolute path to a `enc-{hub_name}.secret.values.yaml` file
    for a named cluster and hub

    Args:
        cluster_name (str): The name of the cluster we wish to perform actions on.
            This corresponds to a folder name, and that folder should contain a
            cluster.yaml file.
        hub_name (str): The name of the hub we wish to perform actions on.
            This hub name must be listed in the cluster's cluster.yaml file.

    Returns:
        Path object: The absolute path to the `enc-{hub_name}.secret.values.yaml`
        in the `cluster_name` named cluster.
        Note that file doesn't need to exist.
    """
    cluster_config_dir_path = find_absolute_path_to_cluster_file(cluster_name).parent
    encrypted_file_path = cluster_config_dir_path.joinpath(
        f"enc-{hub_name}.secret.values.yaml"
    )

    return encrypted_file_path


def persist_config_in_encrypted_file(encrypted_file, new_config):
    """
    Write `config` to `encrypted_file` file.
    If `encrypted_file` doesn't exist, create it first.
    If `encrypted_file` exits, then merge exiting config with `config` and write the merged config to file.
    """
    if Path(encrypted_file).is_file():
        subprocess.check_call(["sops", "--decrypt", "--in-place", encrypted_file])
        with open(encrypted_file, "r+") as f:
            config = yaml.load(f)
            config.update(new_config)
            f.seek(0)
            yaml.dump(config, f)
            f.truncate()
        return subprocess.check_call(
            ["sops", "--encrypt", "--in-place", encrypted_file]
        )

    with open(encrypted_file, "a+") as f:
        yaml.dump(new_config, f)
    return subprocess.check_call(["sops", "--encrypt", "--in-place", encrypted_file])


def remove_jupyterhub_hub_config_key_from_encrypted_file(encrypted_file, key):
    """
    Remove config from the dict `config["jupyterhub"]["hub"]["config"][<key>]`
    in `encrypted_file` (the config is also searched for under daskhub/binderhub prefixes).

    If after removing this config, the file only contains a config dict with empty leaves,
    delete the entire file, as it no longer holds any information.
    """
    _assert_file_exists(encrypted_file)

    with get_decrypted_file(encrypted_file) as decrypted_path:
        with open(decrypted_path) as f:
            config = yaml.load(f)

    daskhub = config.get("basehub", None)
    binderhub = config.get("binderhub", None)
    if daskhub:
        config["basehub"]["jupyterhub"]["hub"]["config"].pop(key)
    elif binderhub:
        config["binderhub"]["jupyterhub"]["hub"]["config"].pop(key)
    else:
        config["jupyterhub"]["hub"]["config"].pop(key)

    def clean_empty_nested_dicts(d):
        if isinstance(d, dict):
            return {
                key: value
                for key, value in (
                    (key, clean_empty_nested_dicts(value)) for key, value in d.items()
                )
                if value
            }
        return d

    remaining_config = clean_empty_nested_dicts(config)

    if remaining_config:
        with open(encrypted_file, "w") as f:
            yaml.dump(remaining_config, f)
            f.truncate()

        subprocess.check_call(["sops", "--encrypt", "--in-place", encrypted_file])
        return

    # If the file only contained configuration for `key`, then we can safely delete it
    Path(encrypted_file).unlink()


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

    # Our convention is that secrets in the repository include "secret" in their filename,
    # so first we check for that
    if "secret" in filename:
        # We must then determine if the file is using sops
        # sops files are JSON/YAML with a `sops` key. So we first check
        # if the file is valid JSON/YAML, and then if it has a `sops` key.
        with open(original_filepath) as f:
            # JSON files output by terraform have hard tabs, the *one* thing that is
            # valid JSON but not valid YAML
            if ext.endswith("json"):
                loader_func = json.load
            else:
                loader_func = yaml.load
            try:
                content = loader_func(f)
            except ScannerError:
                raise ScannerError(
                    "We expect encrypted files to be valid JSON or YAML files."
                )

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
        # The file does not have "secret" in its name, therefore does not need to be
        # decrypted. Yield the original filepath unchanged.
        yield original_filepath


@contextmanager
def get_decrypted_files(files):
    """
    This is a context manager that combines multiple `get_decrypted_file`
    context managers that open and/or decrypt the files in `files`.

    files should be all absolute paths
    """
    with ExitStack() as stack:
        yield [stack.enter_context(get_decrypted_file(f)) for f in files]
