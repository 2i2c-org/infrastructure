from pathlib import Path

import pandas as pd
import typer

from .cost_table_app import cost_table_app


@cost_table_app.command()
def gcp(
    input_path: Path = typer.Argument(
        ..., help="The file path to the cost table downloaded from the GCP UI"
    )
):
    """
    Ingests a CSV cost table generated via the GCP UI and performs a transformation.

    We assume the input CSV file has the following columns (and are subject to
    changes by GCP):
    - Project name
    - Month
    - Subtotal ($)

    We aim to have an output CSV file with columns:
    - Project name
    - start-month
    - ...
    - end-month
    - Total

    where:
    - start-month...end-month are unique values from the Month column in the
      input file
    - Project name are unique entries from the input file
    - The Total column is the sum across all month columns for each project
    """
    # Read the CSV file into a pandas dataframe. Only select relevant columns from
    # the input file: [Project Name, Month, Subtotal ($)]. Rename the columns so
    # that they are all lower case and any whitespace in column names is replaced
    # with an underscore.
    df = pd.read_csv(
        input_filepath, usecols=["Month", "Project name", "Subtotal ($)"]
    ).rename(columns=lambda col: col.strip().lower().replace(" ", "_"))

    # Aggregate and pivot the dataframe into desired format
    transformed_df = (
        # Group the data by project name and month, and sum the subtotals
        df.groupby(["project_name", "month"]).sum()
        # Pivot the data so project name is the index and months are columns
        .pivot_table(index="project_name", columns="month", values="subtotal_($)")
        # Create a new column containing the total across all the months
        .assign(total=lambda df: df.sum(axis=1))
    )
    print(transformed_df)
