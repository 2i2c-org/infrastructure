import tempfile
from pathlib import Path
from ruamel.yaml import YAML
import subprocess
import hashlib
import hmac
import os

from auth import KeyProvider
from hub import Hub

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

HERE = Path(__file__).parent
PROXY_SECRET_KEY = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

AUTH0_DOMAIN = 'yuvipanda.auth0.com'
auth0_token = KeyProvider.get_token(
    AUTH0_DOMAIN,
    os.environ['AUTH0_MANAGEMENT_CLIENT_ID'],
    os.environ['AUTH0_MANAGEMENT_CLIENT_SECRET']
)

k = KeyProvider(AUTH0_DOMAIN, auth0_token)

def load_hubs():
    with open(HERE / "hubs.yaml") as f:
        return yaml.load(f)

hubs = load_hubs()

for hub_yaml in hubs['hubs']:
    hub = Hub(hub_yaml, k, PROXY_SECRET_KEY)
    hub.deploy()