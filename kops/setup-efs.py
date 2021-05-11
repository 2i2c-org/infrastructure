#!/usr/bin/env python3
"""
Hacky script to automate EFS setup for a given kops cluster

1. Create an EFS file system
2. Create a mount target with correct security groups & subnets for
   a given kops cluster
"""

import sys
import boto3
import secrets
import time

def find_subnets(cluster_name, region):
    """
    Find all the subnets created by kops for this cluster
    """
    ec2 = boto3.client('ec2', region_name=region)
    return ec2.describe_subnets(Filters=[
        {'Name':'tag:KubernetesCluster', 'Values': [cluster_name]}
    ])['Subnets']

def find_security_groups(cluster_name, region):
    """
    Find security groups of master and nodes
    """
    ec2 = boto3.client('ec2', region_name=region)
    return ec2.describe_security_groups(Filters=[
        {'Name':'tag:Name', 'Values': [f'{t}.{cluster_name}' for t in ['masters', 'nodes']]}
    ])['SecurityGroups']

def create_filesystem(token, name, region):
    efs = boto3.client('efs', region_name=region)
    subnets = find_subnets(name, region)
    security_groups = find_security_groups(name, region)
    fs = efs.create_file_system(
        CreationToken=token,
        Encrypted=True,
        Backup=True,
        Tags=[
            {'Key': 'KubernetesCluster', 'Value': name}
        ]
    )
    while True:
        resp = efs.describe_file_systems(
            CreationToken=token
        )
        if resp['FileSystems'][0]['LifeCycleState'] == 'available':
            break
        time.sleep(5)

    for subnet in subnets:
        efs.create_mount_target(
            FileSystemId=fs['FileSystemId'],
            SubnetId=subnet['SubnetId'],
            SecurityGroups=[sg['GroupId'] for sg in security_groups]
        )
    print(f'setup {fs["FileSystemId"]}')

if __name__ == '__main__':
    token = secrets.token_hex(16)
    create_filesystem(token, sys.argv[1], sys.argv[2])