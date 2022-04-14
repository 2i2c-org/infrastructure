#!/usr/bin/env python3
"""
Hacky script to automate EFS setup for a given kops cluster

1. Create an EFS file system
2. Create a mount target with correct security groups & subnets for
   a given kops cluster

Should be terraform that runs after kops cluster is created and
fetches VPC / SG / Subnets with data sources instead.
"""

import secrets
import sys
import time

import boto3


def find_subnets(cluster_name, region):
    """
    Find all the subnets created by kops for this cluster
    """
    ec2 = boto3.client("ec2", region_name=region)
    return ec2.describe_subnets(
        Filters=[{"Name": "tag:KubernetesCluster", "Values": [cluster_name]}]
    )["Subnets"]


def find_security_groups(cluster_name, region):
    """
    Find security groups of master and nodes of given cluster.

    The EFS mount target needs to be available to the master node of the
    cluster too - this is where the hub, proxy, and other core pods live.
    The hub-share-creator also runs there.
    """
    ec2 = boto3.client("ec2", region_name=region)
    return ec2.describe_security_groups(
        Filters=[
            {
                "Name": "tag:Name",
                "Values": [f"{t}.{cluster_name}" for t in ["masters", "nodes"]],
            }
        ]
    )["SecurityGroups"]


def create_filesystem(token, cluster_name, region):
    """
    Create an EFS filesystem for given cluster

    Sets up a mount target in the appropriate subnets with correct
    security groups too.
    """
    efs = boto3.client("efs", region_name=region)
    subnets = find_subnets(cluster_name, region)
    security_groups = find_security_groups(cluster_name, region)
    fs = efs.create_file_system(
        CreationToken=token,
        Encrypted=True,
        Backup=True,
        Tags=[{"Key": "KubernetesCluster", "Value": cluster_name}],
    )
    while True:
        resp = efs.describe_file_systems(CreationToken=token)
        if resp["FileSystems"][0]["LifeCycleState"] == "available":
            break
        time.sleep(5)

    for subnet in subnets:
        efs.create_mount_target(
            FileSystemId=fs["FileSystemId"],
            SubnetId=subnet["SubnetId"],
            SecurityGroups=[sg["GroupId"] for sg in security_groups],
        )
    print(f'setup {fs["FileSystemId"]}')


if __name__ == "__main__":
    token = secrets.token_hex(16)
    create_filesystem(token, sys.argv[1], sys.argv[2])
