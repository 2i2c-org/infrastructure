import os
import json
import tempfile
import subprocess
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from contextlib import contextmanager

yaml = YAML(typ="safe", pure=True)


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
