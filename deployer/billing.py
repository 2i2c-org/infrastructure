import re
import sys
from pathlib import PosixPath

from google.cloud import bigquery, billing_v1
from google.cloud.logging_v2.services.config_service_v2 import ConfigServiceV2Client
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

from .cli_app import app
from .helm_upgrade_decision import get_all_cluster_yaml_files

yaml = YAML(typ="safe")

HERE = PosixPath(__file__).parent.parent


@app.command()
def validate_billing_info():
    """
    Validate our billing accounts information

    - All GCP projects mentioned in any hub cluster have an appropriate entry in billing-accounts.yaml
    """

    # Get a list of filepaths to all cluster.yaml files in the repo
    cluster_files = get_all_cluster_yaml_files()

    gcp_projects = set()
    for cf in cluster_files:
        with open(cf) as f:
            cluster = yaml.load(f)
        if cluster["provider"] == "gcp":
            gcp_projects.add(cluster["gcp"]["project"])

    with open(HERE.joinpath("config/billing-accounts.yaml")) as f:
        accounts = yaml.load(f)

    accounts_projects = set()

    for account in accounts["gcp"]["billing_accounts"]:
        for project in account["projects"]:
            accounts_projects.add(project)

    if accounts_projects != gcp_projects:
        print(accounts_projects)
        print("Not all projects in use have invoicing information specified!")
        print(
            f"{','.join(gcp_projects - accounts_projects)} are missing invoicing information"
        )
        sys.exit(1)


# FIXME: This doesn't actually work yet correctly
def validate_billing_export():
    # Get billing accounts info
    with open(HERE.joinpath("config/billing-accounts.yaml")) as f:
        accounts = yaml.load(f)

    # Create a client
    billing_client = billing_v1.CloudBillingClient()

    managed_billing_accounts = {
        a["id"] for a in accounts["gcp"]["billing_accounts"] if a["managed"]
    }
    logging_client = ConfigServiceV2Client()

    # Handle the response
    for ba in managed_billing_accounts:

        # Make the request
        response = billing_client.get_billing_account(
            name=f"billingAccounts/{ba}",
        )
        if not response.open_:
            print(f"Billing account {ba} is closed!")
            sys.exit(1)

        print(f"trying for {ba}")

        # Make the request
        sinks = list(logging_client.list_sinks(parent=f"billingAccounts/{ba}"))

        # Handle the response
        print(sinks)


@app.command()
def generate_cost_table():

    with open(HERE.joinpath("config/billing-accounts.yaml")) as f:
        accounts = yaml.load(f)

    client = bigquery.Client()

    table = Table(title="Project Costs")

    table.add_column("Period", justify="right", style="cyan", no_wrap=True)
    table.add_column("Project", style="white")
    table.add_column("Cost (before credits)", justify="right", style="green")
    table.add_column("Cost (after credits)", justify="right", style="green")

    for a in accounts["gcp"]["billing_accounts"]:
        if "bigquery" not in a:
            print(
                f'No bigquery table specified for billing account {a["id"]}, skipping'
            )
            continue
        bq = a["bigquery"]

        # FIXME: We are using string interpolation here to construct a sql-like query, which
        # IS GENERALLY VERY VERY BAD AND NO GOOD AND WE SHOULD NOT DO IT NO EVER.
        # HOWEVER, I can't seem to find a way to parameterize the *table name* as we must do here,
        # rather than just query parameters. So we *very* carefully construct the name of the table here,
        # and use that in the query. In addition, we allow-list the characters available to the table name as
        # well - and fail hard if something is fishy. This shouldn't really be a problem, as we control the
        # input to this function (via our YAML file). However, SQL Injections are likely to happen in places
        # where you least expect them to happen, so the extra layer of protection is nice.
        table_name = f'{bq["project"]}.{bq["dataset"]}.gcp_billing_export_resource_v1_{a["id"].replace("-", "_")}'
        # Make sure the table name only has alphanumeric characters, _ and -
        assert re.match(r"^[a-zA-Z0-9._-]+$", table_name)
        query = f"""
        SELECT
        invoice.month as month,
        project.id as project,
        SUM(cost)
            AS total_without_credits,
        (SUM(CAST(cost AS NUMERIC))
            + SUM(IFNULL((SELECT SUM(CAST(c.amount AS NUMERIC))
                        FROM UNNEST(credits) AS c), 0)))
            AS total_with_credits
        FROM `{table_name}`
        GROUP BY 1, 2
        ORDER BY 1 ASC
        ;

        """

        rows = client.query(query).result()
        last_month = None
        for r in rows:
            year = r.month[:4]
            month = r.month[4:]
            if not r.project:
                project = f"{a['id']} non-project"
            else:
                project = r.project

            if last_month != None and r.month != last_month:
                table.add_section()
            table.add_row(
                f"{year}-{month}",
                project,
                str(round(r.total_without_credits, 2)),
                str(round(r.total_with_credits, 2)),
            )
            last_month = r.month

    console = Console()
    console.print(table)
