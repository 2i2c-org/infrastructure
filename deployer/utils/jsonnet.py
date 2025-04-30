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
def render_jsonnet(jsonnet_file: Path, jsonnet_search_paths: list[Path]):
    """
    Provide path to rendered json file for given jsonnet file
    """

    command = ["jsonnet", "--jpath", str(jsonnet_file.parent)]
    for jsp in jsonnet_search_paths:
        command += ["--jpath", jsp]
    command += [jsonnet_file]

    print(f"Rendering jsonnet file {jsonnet_file} with the command: ", end="")
    # We print it without the temporary filename so deployers can reuse the command
    print_colour(shlex.join([str(s) for s in command]))

    with NamedTemporaryFile(suffix=".json") as f:
        command += ["--output-file", f.name]

        subprocess.check_call(command)

        yield f.name
