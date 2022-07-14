import os
import subprocess
from textwrap import dedent

from markdownTable import markdownTable


def print_colour(msg: str, colour="green"):
    """Print messages in colour to be distinguishable in CI logs

    See the mybinder.org deploy.py script for more details:
    https://github.com/jupyterhub/mybinder.org-deploy/blob/master/deploy.py

    Args:
        msg (str): The message to print in colour
    """
    if not os.environ.get("TERM"):
        # no term, no colors
        print(msg)

        return

    BOLD = subprocess.check_output(["tput", "bold"]).decode()
    YELLOW = subprocess.check_output(["tput", "setaf", "3"]).decode()
    GREEN = subprocess.check_output(["tput", "setaf", "2"]).decode()
    RED = subprocess.check_output(["tput", "setaf", "1"]).decode()
    NC = subprocess.check_output(["tput", "sgr0"]).decode()

    if colour == "green":
        print(BOLD + GREEN + msg + NC, flush=True)
    elif colour == "red":
        print(BOLD + RED + msg + NC, flush=True)
    elif colour == "yellow":
        print(BOLD + YELLOW + msg + NC, flush=True)
    else:
        # colour not recognized, no colors
        print(msg)


def create_markdown_comment(support_staging_matrix, prod_matrix):
    """Convert a list of dictionaries into a Markdown formatted table for posting to
    GitHub as comments. This function will write the Markdown content to a file to allow
    a GitHub Actions to upload it as an artifact and reuse the content in another
    workflow.

    Args:
        support_staging_matrix (list[dict]): The support of staging jobs to be converted
            into a Markdown formatted table
        prod_matrix (list[dict]): The production jobs to be converted into a Markdown
            formatted table
    """
    # A dictionary to convert column names
    column_converter = {
        "cluster_name": "Cluster Name",
        "provider": "Cloud Provider",
        "upgrade_support": "Upgrade Support?",
        "reason_for_support_redeploy": "Reason for Support Redeploy",
        "upgrade_staging": "Upgrade Staging?",
        "reason_for_staging_redeploy": "Reason for Staging Redeploy",
        "hub_name": "Hub Name",
        "reason_for_redeploy": "Reason for Redeploy",
    }

    # A dictionary to convert row values when they are Boolean
    boolean_converter = {
        True: "Yes",
        False: "No",
    }

    # === To reliably convert a list of dictionaries into a Markdown table, the keys
    # === must be consistent across each dictionary in the list as they will become the
    # === columns of the table. Moreover, we want the columns to be in 'sensible' order
    # === when a human reads this table; therefore, we reformat the inputted jobs.

    # Format the Support and Staging matrix jobs
    formatted_support_staging_matrix = []
    for entry in support_staging_matrix:
        formatted_entry = {
            column_converter["provider"]: entry["provider"],
            column_converter["cluster_name"]: entry["cluster_name"],
            column_converter["upgrade_support"]: boolean_converter[
                entry["upgrade_support"]
            ],
            column_converter["reason_for_support_redeploy"]: entry[
                "reason_for_support_redeploy"
            ],
            column_converter["upgrade_staging"]: boolean_converter[
                entry["upgrade_staging"]
            ],
            column_converter["reason_for_staging_redeploy"]: entry[
                "reason_for_staging_redeploy"
            ],
        }
        formatted_support_staging_matrix.append(formatted_entry)

    # Generate a Markdown table
    support_staging_md_table = (
        markdownTable(formatted_support_staging_matrix)
        .setParams(row_sep="markdown", quote=False)
        .getMarkdown()
    )

    # Format the Support and Staging matrix jobs
    formatted_prod_matrix = []
    for entry in prod_matrix:
        formatted_entry = {
            column_converter["provider"]: entry["provider"],
            column_converter["cluster_name"]: entry["cluster_name"],
            column_converter["hub_name"]: entry["hub_name"],
            column_converter["reason_for_redeploy"]: entry["reason_for_redeploy"],
        }
        formatted_prod_matrix.append(formatted_entry)

    # Generate a Markdown table
    prod_md_table = (
        markdownTable(formatted_prod_matrix)
        .setParams(row_sep="markdown", quote=False)
        .getMarkdown()
    )

    # Create the body of the comment to post
    comment_body = dedent(
        f"""<!-- deployment-plan -->

        ### Support and Staging deployments

        {support_staging_md_table}

        ### Production deployments

        {prod_md_table}
        """
    )

    # Save comment body to a file to be uploaded as an atrifact by GitHub Actions
    with open("comment-body.txt", "w") as f:
        f.write(comment_body)
