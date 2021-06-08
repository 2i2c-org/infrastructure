#!/usr/bin/env python3
"""
Maintain per-cluster support chart

Sets up the following charts:

1. cert-manager (with CRDs), since it can not be
   installed as a dependent chart.
   https://github.com/jetstack/cert-manager/issues/3062#issuecomment-708252281
2. support/, a meta chart that installs nginx-ingress, grafana
   and prometheus.
"""
import shutil
import subprocess
from pathlib import Path
import argparse


CERT_MANAGER_VERSION = 'v1.3.1'
HERE = Path(__file__).parent

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'cluster',
        help='Name of cluster to provision support charts in'
    )

    args = argparser.parse_args()

    print("Provisioning cert-manager...")
    subprocess.check_call([
        'helm', 'upgrade', '--install', '--create-namespace',
        '--namespace', 'cert-manager',
        'cert-manager', 'jetstack/cert-manager',
        '--version', CERT_MANAGER_VERSION,
        '--set', 'installCRDs=true'
    ])
    print("Done!")

    print("Support charts...")

    shutil.rmtree(HERE / 'charts')
    subprocess.check_call([
        'helm', 'dep', 'up', str(HERE)
    ])

    subprocess.check_call([
        'helm', 'upgrade', '--install', '--create-namespace',
        '--namespace', 'support',
        'support', 'support',
        '-f', str(HERE / 'clusters' / (args.cluster + '.yaml')),
        '--wait'
    ])
    print("Done!")

if __name__ == '__main__':
    main()