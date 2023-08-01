"""Pull latest list of hubs features and save as a CSV table.

This is used in two places:

- docs/_static/hub-options-table.json is published with the docs and meant for re-use in other parts of 2i2c
- docs/tmp/hub-options-table.csv is read by reference/hubs.md to create a list of hubs
"""
from utils import get_clusters_list, write_df_to_json_and_csv_files
from yaml import safe_load


def get_hub_authentication(hub_config):
    authenticator_info = ""

    daskhub = hub_config.get("basehub", None)
    binderhub = hub_config.get("binderhub", None)

    # Return the value of `authenticator_class` from the `hub_config` dictionary
    # and the empty string if none is found
    try:
        if daskhub:
            authenticator_info = hub_config["basehub"]["jupyterhub"]["hub"]["config"][
                "JupyterHub"
            ]["authenticator_class"]
        elif binderhub:
            authenticator_info = hub_config["binderhub"]["jupyterhub"]["hub"]["config"][
                "JupyterHub"
            ]["authenticator_class"]
        authenticator_info = hub_config["jupyterhub"]["hub"]["config"]["JupyterHub"][
            "authenticator_class"
        ]
    except KeyError:
        pass

    return authenticator_info


def build_options_list_entry(hub, authenticator):
    return {
        "domain": f"[{hub['domain']}](https://{hub['domain']})",
        "authenticator": authenticator,
        # "user id anonymisation": anonymizeUsername
        #         "admin access to all user's home dirs":
        #         "community domain":
        #         "self-configured login page":
        #         "custom hub pages":
        #         "static web pages":
        #         "gh-scoped-creds":
        #         "shared cluster":
        #         "buckets":
        #         "dask":
        #         "GPUs":
        #         "profile lists":
    }


def main():
    # Grab the latest list of clusters defined in infrastructure/ explicitly ignoring
    # the test clusters in the ./tests directory
    clusters = get_clusters_list()
    options_list = []

    for cluster_info in clusters:
        cluster_path = cluster_info.parent
        if "schema" in cluster_info.name or "staff" in cluster_info.name:
            continue
        # For each cluster, grab it's YAML w/ the config for each hub
        yaml = cluster_info.read_text()
        cluster = safe_load(yaml)

        # For each hub in cluster, grab its metadata and add it to the list
        for hub in cluster["hubs"]:
            hub_values_files = [
                file_name
                for file_name in hub["helm_chart_values_files"]
                if "enc" not in file_name
            ]

            for config_file in hub_values_files:
                with open(cluster_path.joinpath(config_file)) as f:
                    hub_config = safe_load(f)
                authenticator = get_hub_authentication(hub_config)
                if authenticator:
                    break

            options_list.append(build_options_list_entry(hub, authenticator))

    # Write raw data to CSV and JSON
    write_df_to_json_and_csv_files(options_list, "hub-options-table")
    print("Finished updating list of hubs features table...")


if __name__ == "__main__":
    main()
