import tempfile
from pathlib import Path
from ruamel.yaml import YAML
import subprocess
import hashlib
import hmac
import os

from auth import KeyProvider
from hub import Hub, Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

HERE = Path(__file__).parent
PROXY_SECRET_KEY = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

AUTH0_DOMAIN = 'yuvipanda.auth0.com'

k = KeyProvider(
    AUTH0_DOMAIN,
    os.environ['AUTH0_MANAGEMENT_CLIENT_ID'],
    os.environ['AUTH0_MANAGEMENT_CLIENT_SECRET']
)

def load_config():
    with open(HERE / "hubs.yaml") as f:
        return yaml.load(f)

config = load_config()

clusters = {}

for cluster_yaml in config['clusters']:
    cluster = Cluster(cluster_yaml, k)
    cluster_name = cluster_yaml['name']
    with cluster.auth():
        cluster.build_image()
        for hub in cluster.hubs:
            hub.deploy(PROXY_SECRET_KEY)
