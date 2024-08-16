import re
from pathlib import Path

import pandas as pd
import typer

from deployer.cli_app import transform_app
from deployer.utils.rendering import print_colour

# Creates a new typer application, which is then nested as a sub-command named
# "cost-table" under the `transform` sub-command of the deployer.
cost_table_app = typer.Typer(pretty_exceptions_show_locals=False)
transform_app.add_typer(
    cost_table_app,
    name="cost-table",
    help="Transform the cost table from a cloud provider when completing billing cycles",
)


@cost_table_app.command()
def aws(
    input_path: Path = typer.Argument(
        ..., help="The file path to the cost table downloaded from the AWS UI"
    ),
    output_path: Path = typer.Option(
        None,
        help="(Optional) The path to write the output CSV to. If None, one will be constructed.",
    ),
):
    """
    Ingests a CSV cost table generated via the AWS UI and performs a transformation.

    We assume the input CSV has a column for each linked account and rows for:
    - the linked account ID and name
    - a monthly total for each month selected
    - a linked account total across the month range

    We aim to have an output CSV file with columns:
    - linked account name
    - start-month
    - ...
    - end-month
    - linked account total
    """
    # Read the CSV file into a pandas dataframe. Skip the first row and this
    # contains numerical project IDs - the project names begin on the second row.
    df = pd.read_csv(
        input_path,
        skiprows=1,
    )

    # We conditionally rename the column names. If '($)' is present in the column
    # name, we assume this is a linked account name: we strip of any
    # leading/trailing whitespace and convert to lower case so we have just the
    # account names and allow for AWS permitting whitespace in them.
    # Otherwise (i.e. not an account name), we also replace any whitespace with
    # underscores for easier data cleaning in pandas.
    df.rename(
        columns=lambda col: (
            col.lower().strip("($)").strip()
            if "($)" in col
            else col.strip().lower().replace(" ", "_")
        ),
        inplace=True,
    )

    # Ensure values of the linked_account_name column are lower case and any
    # whitespace is replaced with underscores.
    # Note that because AWS outputs the linked account names as a row, this
    # column name is misleading - we are not affecting linked account names here.
    df["linked_account_name"] = df["linked_account_name"].apply(
        lambda val: val.strip().lower().replace(" ", "_")
    )

    # Set the linked_account_name column as the index
    df.set_index("linked_account_name", drop=True, inplace=True)

    # Drop the 'total costs' column. This column is the total across all linked
    # accounts, and hence not necessary. We use the linked_account_total column
    # for the total per linked account.
    df.drop("total costs", axis=1, inplace=True)

    # Transpose the dataframe
    df = df.T

    # Sort the columns
    df = df.reindex(sorted(df.columns), axis=1)

    # Sort the account names in alphabetical order
    df.sort_index(inplace=True)

    # Transform months from 2024-01-01 to 2024-01
    df.rename(
        columns=lambda col: (
            re.match("([0-9]*-[0-9]*)-[0-9]*", col).groups()[0]
            if re.match("[0-9]*-[0-9]*-[0-9]*", col)
            else col
        ),
        inplace=True,
    )

    if output_path is None:
        # Find all the column names that match the regex expression `[0-9]*-[0-9]*`
        months = [
            col for col in df.columns if re.match("[0-9]*-[0-9]*", col) is not None
        ]

        # Construct output filename
        output_path = Path(f"AWS_{months[0]}_{months[-1]}.csv")

    print_colour(f"Writing output CSV to: {output_path}")

    # Save CSV file
    df.to_csv(output_path, index_label="project_name")


@cost_table_app.command()
def gcp(
    input_path: Path = typer.Argument(
        ..., help="The file path to the cost table downloaded from the GCP UI"
    ),
    output_path: Path = typer.Option(
        None,
        help="(Optional) The path to write the output CSV to. If None, one will be constructed.",
    ),
):
    """
    Ingests a CSV cost table generated via the GCP UI and performs a transformation.

    We assume the input CSV file has the following columns (and are subject to
    changes by GCP):
    - Project name
    - Subtotal ($)
    - Month *

    (*) The Month column will be missing if the report is generated for a single month.

    We aim to have an output CSV file with columns:
    - Project name
    - start-month
    - ...
    - end-month
    - Total

    where:
    - start-month...end-month are unique values from the Month column in the
      input file or from the name of the input file if the Month column is missing.
    - Project name are unique entries from the input file
    - The Total column is the sum across all month columns for each project
    """
    df = pd.read_csv(
        input_path,
    )

    # We only need the following columns from the input file
    required_columns = ["Month", "Project name", "Subtotal ($)"]

    # Filter the columns that actually exist in the dataframe
    existing_columns = [col for col in required_columns if col in df.columns]

    # Select only the existing columns and rename them so that they
    # are all lower case and replace any whitespace in column names
    # with an underscore.
    df = df[existing_columns].rename(
        columns=lambda col: col.strip().lower().replace(" ", "_")
    )

    if "Month" not in existing_columns:
        # If group by month wasn't possible, it means we have a single month
        # and we extract it from the file name
        match = re.search(r"(\d{4}-\d{2})-\d{2} — (\d{4}-\d{2})-\d{2}", input_path.name)
        if not match:
            raise ValueError(
                "Month period not found in file name. Try downloading the report again from GCP without renaming it."
            )
        start_month_year = match.group(1)
        end_month_year = match.group(2)
        assert start_month_year == end_month_year

        # Assign the extracted month period to the dataframe
        df = df.assign(month=start_month_year)

    # Aggregate and pivot the dataframe into desired format
    transformed_df = (
        # Group the data by project name and month, and sum the subtotals
        df.groupby(["project_name", "month"]).sum()
        # Pivot the data so project name is the index and months are columns
        .pivot_table(index="project_name", columns="month", values="subtotal_($)")
        # Create a new column containing the total across all the months
        .assign(total=lambda df: df.sum(axis=1))
    )

    if output_path is None:
        # Find all the column names that match the regex expression `[0-9]*-[0-9]*`
        months = [
            col
            for col in transformed_df.columns
            if re.match("[0-9]*-[0-9]*", col) is not None
        ]

        # Construct output filename
        output_path = Path(f"GCP_{months[0]}_{months[-1]}.csv")

    print_colour(f"Writing output CSV to: {output_path}")

    # Save CSV file
    transformed_df.to_csv(output_path)
