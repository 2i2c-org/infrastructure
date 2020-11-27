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


def find_cluster_by_name(cluster_name, clusters):
    """
    Find a cluster by name in a list of Cluster objects
    """
    for cluster in clusters:
        if cluster.spec['name'] == cluster_name:
            return cluster


def find_hub_in_cluster(hub_name, hubs):
    """
    Find a hub by name in a list of Hub objects
    """
    for hub in hubs:
        if hub.spec['name'] == hub_name:
            return hub


def build():
    """
    Build and push all images for all clusters
    """
    clusters = parse_clusters()
    for cluster in clusters:
        with cluster.auth():
            cluster.build_image()


def deploy(cluster_name=None, hub_name=None):
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
        cluster = find_cluster_by_name(cluster_name, clusters)
        with cluster.auth():
            hubs = cluster.hubs
            if hub_name:
                hub = find_hub_in_cluster(hub_name, hubs)
                hub.deploy(k, PROXY_SECRET_KEY)
            else:
                for hub in hubs:
                    hub.deploy(k, PROXY_SECRET_KEY)
    else:
        for cluster in clusters:
            with cluster.auth():
                for hub in cluster.hubs:
                    hub.deploy(k, PROXY_SECRET_KEY)


def main():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest='action')

    build_parser = subparsers.add_parser('build')
    deploy_parser = subparsers.add_parser('deploy')

    deploy_subparsers = deploy_parser.add_subparsers(dest='mode')

    all_parser = deploy_subparsers.add_parser(
        'all-hubs',
        help='Deploy all the hubs'
    )
    hub_parser = deploy_subparsers.add_parser(
        'hub',
        help='Only deploy a specific hub in a cluster'
    )

    hub_parser.add_argument('cluster_name')
    hub_parser.add_argument('hub_name')

    args = argparser.parse_args()

    if args.action == 'build':
        build()
    elif args.action == 'deploy':
        if args.mode == 'all-hubs':
            deploy()
        else:
            deploy(args.cluster_name, args.hub_name)

if __name__ == '__main__':
    main()
