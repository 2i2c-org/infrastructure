from pathlib import Path

path_root = Path(__file__).parent.parent
path_clusters = path_root / "../config/clusters"
path_terraform = path_root / "../terraform/"


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


def get_cluster_provider(cluster):
    custom_providers = {"utoronto": "azure"}
    if cluster["name"] in custom_providers.keys():
        return custom_providers[cluster["name"]]
    return cluster["provider"]


def write_to_json_and_csv_files(info, file_name_prefix):
    # Convert to a DataFrame and write it to a CSV file that will be read by Sphinx
    path_tmp = path_root / "tmp"
    path_static = path_root / "_static"

    path_tmp.mkdir(exist_ok=True)
    path_table = path_tmp / f"{file_name_prefix}.csv"

    info.to_csv(path_table)
    info.to_json(path_static / f"{file_name_prefix}.json", orient="index")
