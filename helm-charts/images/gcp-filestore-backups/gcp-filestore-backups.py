import argparse
import json
import subprocess
import time
from datetime import datetime, timedelta

import jmespath


def main(args):
    # Get a JSON object of the filestore backups. We filter by project and region
    # in the gcloud command.
    filestore_backups = subprocess.check_output(
        [
            "gcloud",
            "filestore",
            "backups",
            "list",
            "--format=json",
            f"--project={args.project}",
            f"--region={args.region}",
        ],
        text=True,
    )
    filestore_backups = json.loads(filestore_backups)

    # Filter returned backups by filestore and share names
    filestore_backups = jmespath.search(
        f"[?sourceFileShare == '{args.filestore_share_name}' && contains(sourceInstance, '{args.filestore_name}')]",
        filestore_backups,
    )

    # Parse `createTime` to a datetime object for comparison
    filestore_backups = [
        {
            k: (
                datetime.strptime(v.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                if k == "createTime"
                else v
            )
            for k, v in backup.items()
        }
        for backup in filestore_backups
    ]

    # Generate a list of filestore backups that are less than 24 hours old
    recent_filestore_backups = [
        backup
        for backup in filestore_backups
        if datetime.now() - backup["createTime"] < timedelta(days=1)
    ]

    # Generate a list of filestore backups that are older than our set retention period
    old_filestore_backups = [
        backup
        for backup in filestore_backups
        if datetime.now() - backup["createTime"] > timedelta(days=args.retention_days)
    ]

    if len(recent_filestore_backups) == 0:
        print(
            f"There have been no recent backups of the filestore for project {args.project}. Creating a backup now..."
        )

        subprocess.check_call(
            [
                "gcloud",
                "filestore",
                "backups",
                "create",
                f"{args.filestore_name}-{args.filestore_share_name}-backup-{datetime.now().strftime('%Y-%m-%d')}",
                f"--file-share={args.filestore_share_name}",
                f"--instance={args.filestore_name}",
                f"--instance-location={args.region}-b",
                f"--region={args.region}",
                # This operation can take a long time to complete and will only take
                # longer as filestores grow, hence we use the `--async` flag to
                # return immediately, without waiting for the operation in progress
                # to complete. Given that we only expect to be creating a backup
                # once a day, this feels safe enough to try for now.
                "--async",
            ]
        )
    else:
        print("Recent backup found.")

    if len(old_filestore_backups) > 0:
        print(
            f"Filestore backups older than {args.retention_days} days have been found. They will be deleted."
        )

        for backup in old_filestore_backups:
            subprocess.check_call(
                [
                    "gcloud",
                    "filestore",
                    "backups",
                    "delete",
                    backup["name"].split("/")[-1],
                    f"--region={args.region}",
                    "--quiet",  # Otherwise we are prompted to confirm deletion
                ]
            )
    else:
        print("No outdated backups found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "project",
        type=str,
        help="",
    )
    parser.add_argument("filestore_name", type=str, help="")
    parser.add_argument(
        "region",
        type=str,
        help="",
    )
    parser.add_argument(
        "--filestore-share-name",
        type=str,
        default="homes",
        help="",
    )
    parser.add_argument("--retention-days", type=int, default=5, help="")

    args = parser.parse_args()

    while True:
        main(args)
        time.sleep(600)  # 60 seconds * 10 for 10 minutes sleep period
