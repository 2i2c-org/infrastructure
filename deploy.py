"""
Deploy many JupyterHubs to manny Kubernetes Clusters
"""
import tempfile
from pathlib import Path
from ruamel.yaml import YAML
import subprocess
import hashlib
import hmac
import os
import argparse
import asyncio

from auth import KeyProvider
from hub import Hub, Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ='safe', pure=True)

def parse_clusters():
    """
    Parse hubs.yaml file & return a list of Clusters
    """
    with open(Path(__file__).parent / "hubs.yaml") as f:
        config = yaml.load(f)

    return [
        Cluster(cluster_yaml)
        for cluster_yaml in config['clusters']
    ]


def build():
    """
    Build and push all images for all clusters
    """
    clusters = parse_clusters()
    for cluster in clusters:
        with cluster.auth():
            cluster.build_image()


async def deploy(cluster_name, hub_name, test_notebook_path):
    """
    Deploy all hubs in all clusters
    """

    # All our hubs use Auth0 for Authentication. This lets us programmatically
    # determine what auth provider each hub uses - GitHub, Google, etc. Without
    # this, we'd have to manually generate credentials for each hub - and we
    # don't want to do that. Auth0 domains are tied to a account, and
    # this is our auth0 domain for the paid account that 2i2c has.
    AUTH0_DOMAIN = '2i2c.us.auth0.com'

    k = KeyProvider(
        AUTH0_DOMAIN,
        os.environ['AUTH0_MANAGEMENT_CLIENT_ID'],
        os.environ['AUTH0_MANAGEMENT_CLIENT_SECRET']
    )

    # Each hub needs a unique proxy.secretToken. However, we don't want
    # to manually generate & save it. We also don't want it to change with
    # each deploy - that causes a pod restart with downtime. So instead,
    # we generate it based on a signle secret key (`PROXY_SECRET_KEY`)
    # combined with the name of each hub. This way, we get unique,
    # cryptographically secure proxy.secretTokens without having to
    # keep much state. We can rotate them by changing `PROXY_SECRET_KEY`.
    # However, if `PROXY_SECRET_KEY` leaks, that means all the hub's
    # proxy.secretTokens have leaked. So let's be careful with that!
    PROXY_SECRET_KEY = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

    clusters = parse_clusters()

    if cluster_name:
        cluster = next((cluster for cluster in clusters if cluster.spec['name'] == cluster_name), None)
        with cluster.auth():
            hubs = cluster.hubs
            if hub_name:
                hub = next((hub for hub in hubs if hub.spec['name'] == hub_name), None)
                await hub.deploy(k, PROXY_SECRET_KEY, test_notebook_path)
            else:
                for hub in hubs:
                    await hub.deploy(k, PROXY_SECRET_KEY, test_notebook_path)
    else:
        for cluster in clusters:
            with cluster.auth():
                for hub in cluster.hubs:
                    await hub.deploy(k, PROXY_SECRET_KEY, test_notebook_path)


async def main():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest='action')

    build_parser = subparsers.add_parser('build')
    deploy_parser = subparsers.add_parser('deploy')

    deploy_parser.add_argument('cluster_name', nargs="?")
    deploy_parser.add_argument('hub_name', nargs="?")
    deploy_parser.add_argument('--test-notebook-path')

    args = argparser.parse_args()

    if args.action == 'build':
        build()
    elif args.action == 'deploy':
        await deploy(args.cluster_name, args.hub_name, args.test_notebook_path)

if __name__ == '__main__':
    asyncio.run(main())
