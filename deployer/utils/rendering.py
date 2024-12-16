import os
import subprocess

from py_markdown_table.markdown_table import markdown_table


def print_colour(msg: str, colour="green"):
    """Print messages in colour to be distinguishable in CI logs

    See the mybinder.org deploy.py script for more details:
    https://github.com/jupyterhub/mybinder.org-deploy/blob/main/deploy.py

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


def create_markdown_comment(support_matrix, staging_matrix, prod_matrix):
    """Convert a list of dictionaries into a Markdown formatted table for posting to
    GitHub as comments. This function will write the Markdown content to a file to allow
    a GitHub Actions to upload it as an artifact and reuse the content in another
    workflow.

    Args:
        support_matrix (list[dict]): The support jobs to be converted into a Markdown
            formatted table
        staging_matrix (list[dict]): The staging jobs to be converted into a Markdown
            formatted table
        prod_matrix (list[dict]): The production jobs to be converted into a Markdown
            formatted table
    """
    # A dictionary to convert column names
    column_converter = {
        "cluster_name": "Cluster Name",
        "provider": "Cloud Provider",
        "upgrade_support": "Upgrade Support?",
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

    # Only execute if support_matrix is not an empty list
    if support_matrix:
        # Format the Support matrix jobs
        formatted_support_matrix = []
        for entry in support_matrix:
            formatted_entry = {
                column_converter["provider"]: entry["provider"],
                column_converter["cluster_name"]: entry["cluster_name"],
                column_converter["upgrade_support"]: boolean_converter[
                    entry["upgrade_support"]
                ],
                column_converter["reason_for_redeploy"]: entry[
                    "reason_for_redeploy"
                ],
            }
            formatted_support_matrix.append(formatted_entry)

        # Generate a Markdown table
        support_md_table = (
            markdown_table(formatted_support_matrix)
            .set_params(row_sep="markdown", quote=False)
            .get_markdown()
        )
    else:
        support_md_table = []

    # Only execute if staging_matrix is not an empty list
    if staging_matrix:
        # Format the Staging Hubs matrix jobs
        formatted_staging_matrix = []
        for entry in staging_matrix:
            formatted_entry = {
                column_converter["provider"]: entry["provider"],
                column_converter["cluster_name"]: entry["cluster_name"],
                column_converter["hub_name"]: entry["hub_name"],
                column_converter["reason_for_redeploy"]: entry["reason_for_redeploy"],
            }
            formatted_staging_matrix.append(formatted_entry)

        # Generate a Markdown table
        staging_md_table = (
            markdown_table(formatted_staging_matrix)
            .set_params(row_sep="markdown", quote=False)
            .get_markdown()
        )
    else:
        staging_md_table = []

    # Only execute if prod_matrix is not an empty list
    if prod_matrix:
        # Format the Production Hubs matrix jobs
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
            markdown_table(formatted_prod_matrix)
            .set_params(row_sep="markdown", quote=False)
            .get_markdown()
        )
    else:
        prod_md_table = []

    # Create the body of the comment to post
    comment_body = f"""<!-- deployment-plan -->
Merging this PR will trigger the following deployment actions.

### Support deployments

{support_md_table if bool(support_md_table) else 'No support upgrades will be triggered'}

### Staging deployments

{staging_md_table if bool(staging_md_table) else 'No staging hub upgrades will be triggered'}

### Production deployments

{prod_md_table if bool(prod_md_table) else 'No production hub upgrades will be triggered'}
"""

    # Save comment body to a file to be uploaded as an atrifact by GitHub Actions
    with open("comment-body.txt", "w") as f:
        f.write(comment_body)
