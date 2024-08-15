"""
Helper script to verify home directories are being backed up correctly

GCP
---
Wraps a gcloud command to list existing backups of a Fileshare
"""

import json
import subprocess
from datetime import datetime, timedelta

import jmespath
import typer

from deployer.cli_app import verify_backups_app
from deployer.utils.rendering import print_colour


def get_existing_gcp_backups(
    project: str, region: str, filestore_name: str, filestore_share_name: str
):
    """List existing backups of a share on a filestore using the gcloud CLI.
    We filter the backups based on:
    - GCP project
    - GCP region
    - Filestore name
    - Filestore share name

    Args:
        project (str): The GCP project the filestore is located in
        region (str): The region the filestore is located in, e.g., us-central1
        filestore_name (str): The name of the filestore instance
        filestore_share_name (str): The name of the share on the filestore instance

    Returns:
        list(dict): A JSON-like object, where each dict-entry in the list describes
            an existing backup of the filestore
    """
    # Get all existing backups in the selected project and region
    backups = subprocess.check_output(
        [
            "gcloud",
            "filestore",
            "backups",
            "list",
            "--format=json",
            f"--project={project}",
            f"--region={region}",
        ],
        text=True,
    )
    backups = json.loads(backups)

    # Filter returned backups by filestore and share names
    backups = jmespath.search(
        f"[?sourceFileShare == '{filestore_share_name}' && contains(sourceInstance, '{filestore_name}')]",
        backups,
    )

    # Parse `createTime` property into a datetime object for comparison
    backups = [
        {
            k: (
                datetime.strptime(v.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                if k == "createTime"
                else v
            )
            for k, v in backup.items()
        }
        for backup in backups
    ]

    return backups


def filter_gcp_backups_into_recent_and_old(
    backups: list, backup_freq_days: int, retention_days: int
):
    """Filter the list of backups into two groups:
    - Recently created backups that were created within our backup window,
      defined by backup_freq_days
    - Out of date back ups that are older than our retention window, defined by
      retention days

    Args:
        backups (list(dict)): A JSON-like object defining the existing backups
            for the filestore and share we care about
        backup_freq_days (int, optional): The time period in days for which we
            create a backup
        retention_days (int): The number of days above which a backup is considered
            to be out of date

    Returns:
        recent_backups (list(dict)): A JSON-like object containing all existing
            backups with a `createTime` within our backup window
        old_backups (list(dict)): A JSON-like object containing all existing
            backups with a `createTime` older than our retention window
    """
    # Generate a list of filestore backups that are younger than our backup window
    recent_backups = [
        backup
        for backup in backups
        if datetime.now() - backup["createTime"] < timedelta(days=backup_freq_days)
    ]

    # Generate a list of filestore backups that are older than our set retention period
    old_backups = [
        backup
        for backup in backups
        if datetime.now() - backup["createTime"] > timedelta(days=retention_days)
    ]

    return recent_backups, old_backups


@verify_backups_app.command()
def gcp(
    project: str = typer.Argument(
        ..., help="The GCP project the filestore is located in"
    ),
    region: str = typer.Argument(
        ..., help="The GCP region the filestore is located in, e.g., us-central1"
    ),
    filestore_name: str = typer.Argument(
        ..., help="The name of the filestore instance to verify backups of"
    ),
    filestore_share_name: str = typer.Option(
        "homes", help="The name of the share on the filestore"
    ),
    backup_freq_days: int = typer.Option(
        1, help="How often, in days, backups should be created"
    ),
    retention_days: int = typer.Option(
        5, help="How old, in days, backups are allowed to become before being deleted"
    ),
):
    filestore_backups = get_existing_gcp_backups(
        project, region, filestore_name, filestore_share_name
    )
    recent_filestore_backups, old_filestore_backups = (
        filter_gcp_backups_into_recent_and_old(
            filestore_backups, backup_freq_days, retention_days
        )
    )

    if len(recent_filestore_backups) > 0:
        print_colour(
            f"A backup has been made within the last {backup_freq_days} day(s)!"
        )
    else:
        print_colour(
            f"No backups have been made in the last {backup_freq_days} day(s)!",
            colour="red",
        )

    if len(old_filestore_backups) > 0:
        print_colour(
            f"Filestore backups older than {retention_days} day(s) have been found!",
            colour="red",
        )
    else:
        print_colour("No out-dated backups have been found!")
