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
    provider = cluster["provider"]
    if provider == "kubeconfig":
        # Kubeconfig means we manually provision kubernetes
        # So we need to infer the cloud provider from the dashboard URL.
        url = cluster.get("provider_url", "")
        if "jetstream" in url:
            return "jetstream2"
        if "azure" in url:
            return "azure"
        # In case we add another kubeconfig usecase in future
        return "kubeconfig"
    return provider


def write_json_and_table_files(info, file_name_prefix):
    path_tmp = path_root / "tmp"
    path_static = path_root / "_static"
    path_tmp.mkdir(exist_ok=True)

    # NOTE: # Note: as of 2026-06-29 the community-reports repo is the only one that
    # uses the .json files. If it stops using them, we should just stop
    # publishing them to reduce the number of sources of truth for this.
    info.to_json(path_static / f"{file_name_prefix}.json", orient="index")

    # mystmd's csv-table can't include .csv files, so write the CSV directive into
    # a .md file that reference/hubs.md pulls in with {include}.
    # ref: https://github.com/jupyter-book/mystmd/issues/2573
    (path_tmp / f"{file_name_prefix}.md").write_text(
        f"```{{csv-table}}\n:header-rows: 1\n\n{info.to_csv()}```\n"
    )
