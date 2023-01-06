"""
### Summary

This is a helper script that will tell us how many duplicated auth apps we
currently have on Auth0

### Requirements

All requirements are already listed in `requirements.txt` with the exception of
rich, which is listed in `dev-requirements.txt`.

### Running the script

Execute the script from the root of the repository:

- python extra_scripts/count-auth0-apps.py

This will output to the console a list of app names that have more than one
client id (i.e. they have duplicates)

Adding the purge flag will delete apps on Auth0 until each app name only has one
client id associated with it

- python extra_scripts/count-auth0-apps.py --purge
"""

import json
import os
import subprocess
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from rich import print
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

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


def get_auth0_inst(domain, client_id, client_secret):
    """
    Return an authenticated Auth0 instance
    """
    gt = GetToken(domain)
    creds = gt.client_credentials(client_id, client_secret, f"https://{domain}/api/v2/")
    auth0_inst = Auth0(domain, creds["access_token"])
    return auth0_inst


# Read in the auth0 client id and secret from a file
root_dir = Path(__file__).parent.parent
auth0_secret_path = os.path.join(root_dir, "config", "secrets.yaml")
with decrypt_file(auth0_secret_path) as decrypted_file_path:
    with open(decrypted_file_path) as f:
        auth0_config = yaml.load(f)

# Create an authenticated auth0 instance using above creds
auth0_inst = get_auth0_inst(
    auth0_config["auth0"]["domain"],
    auth0_config["auth0"]["client_id"],
    auth0_config["auth0"]["client_secret"],
)

# Get a dictionary of all apps currently active on Auth0. Where there is more
# than one app with the same name, append the client_id to a list
clients = defaultdict(list)
for client in auth0_inst.clients.all(per_page=100):
    clients[client["name"]].append(client["client_id"])

# Filter the dictionary so we only have entries where len(value) > 1
filtered_clients = {k: v for k, v in clients.items() if len(v) > 1}

if len(filtered_clients) > 0:
    # Print the names of the apps that have duplicates and total number of apps
    print("[bold blue]Clients with duplicated Auth0 apps:[/bold blue]")
    for k, v in sorted(filtered_clients.items()):
        print(f"\t{k}: {len(v)}")

else:
    print("[bold green]There are no duplicated Auth0 apps![/bold green] :tada:")

# ===
# This section of the script currently does not work as intended as the
# auth0 client available in config/secrets.yaml is not configured with the
# clients.delete scope.
# ===
# if "--purge" in sys.argv[1:]:
#     print(
#         "[bold red]YOU HAVE OPTED TO PURGE THE DUPLICATED APPS. THIS ACTION CANNOT BE UNDONE. ARE YOU SURE YOU WANT TO PROCEED?[/bold red]"
#     )
#     resp = input("Only 'yes' will be accepted > ")

#     if resp == "yes":
#         for app_name in filtered_clients.keys():
#             while len(filtered_clients[app_name]) > 1:
#                 print(
#                     f":fire: [bold red]Purging[/bold red] {app_name}:{filtered_clients[app_name][-1]}"
#                 )
#                 auth0_inst.clients.delete(filtered_clients[app_name][-1])
#                 del filtered_clients[app_name][-1]

#         print("[blue]Duplicated apps deleted![/blue] :tada:")
#         print(
#             "[bold green]You should now redeploy all hubs to ensure they have the correct Auth0 tokens![/bold green]"
#         )

#     else:
#         import sys
#
#         print("[blue]Exiting without purging[/blue]")
#         sys.exit()
