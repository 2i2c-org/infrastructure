from pathlib import Path

import pandas as pd

path_root = Path(__file__).parent.parent
path_clusters = path_root / "../config/clusters"


def get_clusters_list():
    """
    Grab the latest list of clusters defined in infrastructure/ explicitly ignoring
    the test clusters in the ./tests directory
    """

    return [
        filepath
        for filepath in path_clusters.glob("**/*cluster.yaml")
        if "tests/" not in str(filepath) and "templates" not in str(filepath)
    ]


def turn_list_into_df(list):
    return pd.DataFrame(list)


def write_list_to_json_and_csv_files(list, file_name_prefix):
    # Convert to a DataFrame and write it to a CSV file that will be read by Sphinx
    path_tmp = path_root / "tmp"
    path_static = path_root / "_static"

    df = turn_list_into_df(list)

    path_tmp.mkdir(exist_ok=True)
    path_table = path_tmp / f"{file_name_prefix}.csv"

    df.to_csv(path_table, index=None)
    df.to_json(path_static / f"{file_name_prefix}.json", orient="index")
