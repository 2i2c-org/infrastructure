"""
Utility functions for rendering .jsonnet files into .json files
"""

import shlex
from pathlib import Path
import subprocess
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from ..utils.rendering import print_colour


@contextmanager
def render_jsonnet(
    jsonnet_file: Path,
    jsonnet_search_paths: list[Path]
):
    """
    Provide path to rendered json file for given jsonnet file
    """
    command = [
        "jsonnet",
        "--jpath", str(jsonnet_file.parent)
    ]
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