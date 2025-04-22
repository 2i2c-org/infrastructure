"""
Utility functions for rendering .jsonnet files into .json files
"""

from pathlib import Path
import subprocess
from contextlib import contextmanager
from tempfile import NamedTemporaryFile


@contextmanager
def render_jsonnet(
    jsonnet_path: Path,
):
    """
    Provide path to rendered json file for given jsonnet file
    """
    command = [
        "jsonnet",
        jsonnet_path
    ]
    with NamedTemporaryFile(suffix=".json") as f:
        command += ["--output-file", f.name]

    subprocess.check_call(command)

    yield f.name