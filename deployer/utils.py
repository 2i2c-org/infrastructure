import functools
import json
import os
import subprocess
import tempfile
import warnings
from contextlib import contextmanager, ExitStack
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

yaml = YAML(typ="safe", pure=True)
helm_charts_dir = Path(__file__).parent.parent.joinpath("helm-charts")


def assert_file_exists(filepath):
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
    assert_file_exists(original_filepath)
    filename = os.path.basename(original_filepath)
    _, ext = os.path.splitext(filename)

    # Our convention is that encrypted secrets in the repository begin with "enc-" and include
    # "secret" in the filename, so first we check for that. We use an 'or' conditional here since
    # we want to catch files that contain "secret" but do not have the "enc-" prefix and ensure
    # they are encrypted, raising an error if not.
    if filename.startswith("enc-") or ("secret" in filename):
        # We must then determine if the file is using sops
        # sops files are JSON/YAML with a `sops` key. So we first check
        # if the file is valid JSON/YAML, and then if it has a `sops` key
        with open(original_filepath) as f:

            # Support the (clearly wrong) people who use .yml instead of .yaml
            if ext == ".yaml" or ext == ".yml":
                try:
                    content = yaml.load(f)
                except ScannerError:
                    yield original_filepath
                    return
            elif ext == ".json":
                try:
                    content = json.load(f)
                except json.JSONDecodeError:
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
        return


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


@functools.lru_cache
def _generate_values_schema_json(helm_chart_dir):
    """
    This script reads the values.schema.yaml files part of our Helm charts and
    generates a values.schema.json that can allowing helm the CLI to perform
    validation of passed values before rendering templates or making changes in k8s.

    FIXME: Currently we have a hard coupling between the deployer script and the
           Helm charts part of this repo. Managing the this logic here is a
           compromise but it should really be managed as part of packaging it
           and uploading it to a helm chart registry instead.
    """
    values_schema_yaml = os.path.join(helm_chart_dir, "values.schema.yaml")
    values_schema_json = os.path.join(helm_chart_dir, "values.schema.json")

    with open(values_schema_yaml) as f:
        schema = yaml.load(f)
    with open(values_schema_json, "w") as f:
        json.dump(schema, f)


@functools.lru_cache
def prepare_helm_charts_dependencies_and_schemas():
    """
    Ensures that the helm charts we deploy, basehub and daskhub, have got their
    dependencies updated and .json schema files generated so that they can be
    rendered during validation or deployment.
    """
    basehub_dir = helm_charts_dir.joinpath("basehub")
    _generate_values_schema_json(basehub_dir)
    subprocess.check_call(["helm", "dep", "up", basehub_dir])

    daskhub_dir = helm_charts_dir.joinpath("daskhub")
    _generate_values_schema_json(daskhub_dir)
    subprocess.check_call(["helm", "dep", "up", daskhub_dir])


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
