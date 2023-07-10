from datetime import datetime, timedelta

import pandas as pd
import typer
from dateutil.relativedelta import relativedelta
from ruamel.yaml import YAML

from ..cli_app import app
from ..helm_upgrade_decision import get_all_cluster_yaml_files
from .importers import get_cluster_costs
from .outputers import CostTableOutputFormats, output_cost_table

yaml = YAML(typ="safe", pure=True)


@app.command()
def generate_cost_table(
    start_month: datetime = typer.Option(
        (datetime.utcnow() - relativedelta(months=3)).replace(day=1),
        help="Starting month (as YYYY-MM) to produce cost data for. Defaults to 3 invoicing months ago.",
        formats=["%Y-%m"],
    ),
    end_month: datetime = typer.Option(
        datetime.utcnow().replace(day=1) - timedelta(days=1),
        help="Ending month (as YYYY-MM) to produce cost data for. Defaults to previous invoicing month",
        formats=["%Y-%m"],
    ),
    output: CostTableOutputFormats = typer.Option(
        CostTableOutputFormats.terminal,
        help="Where to output the cost table to",
    ),
    google_sheet_url: str = typer.Option(
        "https://docs.google.com/spreadsheets/d/1T6BJkAhlLtK4U6YB5pVPQKpVej_La0pvG3AlzDOAJ60/edit#gid=0",
        help="Write to given Google Sheet URL. Used when --output is google-sheet. billing-spreadsheet-writer@two-eye-two-see.iam.gserviceaccount.com should have Editor rights on this spreadsheet.",
    ),
):
    """
    Generate table with cloud costs for all GCP projects we pass costs through for.
    """

    cluster_files = get_all_cluster_yaml_files()
    rows = pd.DataFrame()

    for cf in cluster_files:
        with open(cf) as f:
            cluster = yaml.load(f)
        if cluster["provider"] != "gcp":
            # We only support GCP for now
            continue

        if not cluster["gcp"]["billing"]["paid_by_us"]:
            continue

        result = get_cluster_costs(cluster, start_month, end_month)
        rows = pd.concat([rows, result])

    output_cost_table(output, google_sheet_url, rows.sort_index())
