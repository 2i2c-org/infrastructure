import os
import json
import tempfile
import subprocess
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from contextlib import contextmanager

yaml = YAML(typ='safe', pure=True)

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
        if ext == '.yaml' or ext == '.yml':
            try:
                encrypted_data = yaml.load(f)
            except ScannerError:
                yield encrypted_path
                return
        elif ext == '.json':
            try:
                encrypted_data = json.load(f)
            except json.JSONDecodeError:
                yield encrypted_path
                return

    if 'sops' not in encrypted_data:
        yield encrypted_path
        return

    # If file has a `sops` key, we assume it's sops encrypted
    with tempfile.NamedTemporaryFile() as f:
        subprocess.check_call([
            'sops',
            '--output', f.name,
            '--decrypt', encrypted_path
        ])
        yield f.name

def flatten_list(inputlist):
    """
    Flatten a list of strings and lists into a flat list of strings.
    This will only work 1-level deep.
    """
    if isinstance(inputlist, str):
        inputlist = [inputlist]
    out = []
    for ii in inputlist:
        if isinstance(ii, str):
            out.append(ii)
        else:
            out.extend(ii)
    return out

def clean_authenticator_config(config):
    """Prepare a hub's configuration file for deployment."""

    # Flatten authenticated user list since YAML references don't extend, they append
    authenticator = config.get("jupyterhub", {}).get("hub", {}).get("config", {}).get("Authenticator", {})

    # `allowed_users` doesn't exist for hubs where all users are allowed
    if authenticator.get("allowed_users", None):
        authenticator["allowed_users"] = flatten_list(authenticator["allowed_users"])

    authenticator["admin_users"] = flatten_list(authenticator["admin_users"])
