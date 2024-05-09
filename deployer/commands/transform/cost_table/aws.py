from pathlib import Path

import pandas as pd
import typer

from .cost_table_app import cost_table_app


@cost_table_app.command()
def aws(
    input_path: Path = typer.Argument(
        ..., help="The file path to the cost table downloaded from the AWS UI"
    )
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
    # Rename the columns so that they are all lower case and any whitespace is
    # replaced with underscores. Then strip '_($)' to ensure we just have the
    # project names.
    df = pd.read_csv(
        input_path, skiprows=1,
    ).rename(
        columns=lambda col: col.strip().lower().replace(" ", "_").strip("_($)")
    )

    # Ensure values of the linked_account_name column are lower case and any
    # whitespace is replaced with underscores.
    df["linked_account_name"] = df["linked_account_name"].apply(
        lambda val: val.strip().lower().replace(" ", "_")
    )

    # Set the linked_account_name column as the index
    df.set_index("linked_account_name", drop=True, inplace=True)

    # Drop the total_costs column
    df.drop("total_costs", axis=1, inplace=True)

    # Transpose the dataframe
    df = df.T

    # Sort the columns
    df = df.reindex(sorted(df.columns), axis=1)

    # Sort the account names in alphabetical order
    df.sort_index(inplace=True)

    print(df)
