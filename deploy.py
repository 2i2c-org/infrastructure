import tempfile
from pathlib import Path
from ruamel.yaml import YAML
import subprocess
import hashlib
import hmac
import os
import argparse

from auth import KeyProvider
from hub import Hub, Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

HERE = Path(__file__).parent
PROXY_SECRET_KEY = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

AUTH0_DOMAIN = '2i2c.us.auth0.com'

def parse_clusters():
    with open(HERE / "hubs.yaml") as f:
        config = yaml.load(f)

    return [
        Cluster(cluster_yaml)
        for cluster_yaml in config['clusters']
    ]


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'action',
        choices=['build', 'deploy']
    )

    args = argparser.parse_args()


    if args.action == 'build':
        build()
    elif args.action == 'deploy':
        deploy()


def build():
    clusters = parse_clusters()
    for cluster in clusters:
        with cluster.auth():
            cluster.build_image()

def deploy():
    k = KeyProvider(
        AUTH0_DOMAIN,
        os.environ['AUTH0_MANAGEMENT_CLIENT_ID'],
        os.environ['AUTH0_MANAGEMENT_CLIENT_SECRET']
    )

    clusters = parse_clusters()
    for cluster in clusters:
        with cluster.auth():
            for hub in cluster.hubs:
                hub.deploy(k, PROXY_SECRET_KEY)


if __name__ == '__main__':
    main()
