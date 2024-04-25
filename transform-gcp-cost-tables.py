"""
Script that ingests a CSV cost table generated via the GCP UI and performs a
transformation.

We assume the input CSV file has the following columns (and are subject to changes
by GCP):
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
- start-month...end-month are unique values from the Month column in the input file
- Project name are unique entries from the input file
- The Total column is the sum across all month columns for each project
"""

from sys import argv
from pathlib import Path
import pandas as pd

# Get input file path from command line args
input_filepath = Path(argv[1])

# Read input file
input_cost_table = pd.read_csv(
    input_filepath,
    usecols=["Month", "Project name", "Subtotal ($)"],
)

# Drop NaN values
input_cost_table = input_cost_table.dropna()

# Rename the projects column. This makes using the 'query' function later easier
# as we don't have to deal with a column name containing whitespace.
input_cost_table["projects"] = input_cost_table["Project name"]
input_cost_table.drop(columns=["Project name"], inplace=True)

# Get unique months
months = sorted(input_cost_table["Month"].unique().tolist())

# Get unique projects
projects = sorted(input_cost_table["projects"].unique().tolist())

# Construct column headers and target DataFrame for transposition
columns =["Project name"] + months
transposed_cost_table = pd.DataFrame(columns=columns)

# For each project, extract the subtotal for each month and construct a new
# entry in the target transposed dataframe
for project in projects:
    # Begin a new dictionary to contain the billing information for this project
    data = {"Project name": project}

    for month in months:
        # Find the subtotal amount incurred by the current iteration project
        # during the current iteration month
        query = f"projects=='{project}' & Month=='{month}'"
        monthly_total = input_cost_table.query(query)["Subtotal ($)"].item()

        # Store the monthly total in the data dictionary
        data[month] = monthly_total

    # Concatenate the project-specific dataframe into our target transposed data frame
    transposed_cost_table = pd.concat(
        [transposed_cost_table, pd.DataFrame(data, index=[0])],
        ignore_index=True,
    )

# Make the project names the index
transposed_cost_table.set_index("Project name", drop=True, inplace=True)

# Calculate the total over all months
transposed_cost_table["Total"] = transposed_cost_table.sum(axis=1)
print(transposed_cost_table)
