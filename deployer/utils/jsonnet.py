"""
Utility functions for rendering .jsonnet files into .json files
"""

import shlex
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..utils.rendering import print_colour


def validate_jsonnet_version():
    # Check to make sure we're using go-jsonnet, not c++-jsonnet
    # The C++ version has a bug https://github.com/google/jsonnet/issues/1109
    # that makes it unusable for us
    version_info = subprocess.check_output(["jsonnet", "--version"]).decode()

    if "Go implementation" not in version_info:
        print_colour("You need the Go version of jsonnet", "red")
        print_colour(
            "See https://github.com/google/go-jsonnet?tab=readme-ov-file#installation-instructions for install instructions",
            "red",
        )
        sys.exit(1)


@contextmanager
def render_jsonnet(
    jsonnet_file: Path,
    cluster_name: str,
    hub_name: str = None,
    provider: str = None,
    aws_account_id: str = None,
):
    """
    Provide path to rendered json file for given jsonnet file

    The following variables are passed as extVars to jsonnet:
        - cluster_name
        - provider
        - hub_name (optional)

    The following variables are passed as top-level arguments to jsonnet:
        - aws_account_id (optional)

    Be careful in adding more arguments, as that may cause right to replicate issues.
    """
    command = [
        "jsonnet",
        "--jpath",
        str(jsonnet_file.parent),
        "--ext-str",
        f"2I2C_VARS.CLUSTER_NAME={cluster_name}",
    ]
    if hub_name is not None:
        command += ["--ext-str", f"2I2C_VARS.HUB_NAME={hub_name}"]
    if provider is not None:
        command += ["--ext-str", f"2I2C_VARS.PROVIDER={provider}"]
    if aws_account_id is not None:
        command += ["--tla-str", f"aws_account_id={aws_account_id}"]
    # Make the jsonnet file passed be an absolute path, but do not *resolve*
    # it - so symlinks are resolved by jsonnet rather than us. This is important
    # for daskhub compatibility.
    command += [jsonnet_file.absolute()]

    print(f"Rendering jsonnet file {jsonnet_file} with the command: ", end="")
    # We print it without the temporary filename so deployers can reuse the command
    print_colour(shlex.join([str(s) for s in command]))

    with NamedTemporaryFile(suffix=".json") as f:
        command += ["--output-file", f.name]

        subprocess.check_call(command)

        yield f.name
