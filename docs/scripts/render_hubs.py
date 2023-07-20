"""Pull latest list of hubs served by infrastructure/ and save as a CSV table.

This is used in two places:

- docs/_static/hub-table.json is published with the docs and meant for re-use in other parts of 2i2c
- docs/tmp/hub-table.csv is read by reference/hubs.md to create a list of hubs
"""
from pathlib import Path

import pandas as pd
from yaml import safe_load

path_root = Path(__file__).parent.parent
path_tmp = path_root / "tmp"
path_static = path_root / "_static"
path_clusters = path_root / "../config/clusters"


def get_cluster_grafana_url(cluster, cluster_path):
    # Pull support chart information to populate fields (if it exists)
    support_files = cluster.get("support", {}).get("helm_chart_values_files", None)

    if not support_files:
        return ""

    # Loop through support files, look for Grafana config, and grab the URL
    for support_file in support_files:
        with open(cluster_path.joinpath(support_file)) as f:
            support_config = safe_load(f)

        grafana_url = (
            support_config.get("grafana", {}).get("ingress", {}).get("hosts", "")
        )
        # If we find a grafana url, set it here and break the loop, we are done
        if isinstance(grafana_url, list):
            grafana_url = grafana_url[0]
            return f"[{grafana_url}](http://{grafana_url})"

    # In case we don't find any Grafana config, use an empty string as default
    return ""


def get_cluster_console_url(cluster, provider, account, datacentre_loc):
    cluster_console_url = ""

    if provider == "gcp":
        gcp_cluster = cluster["gcp"]["cluster"]
        gcp_project = cluster["gcp"]["project"]
        cluster_console_url = (
            f"https://console.cloud.google.com/kubernetes/clusters/details/{datacentre_loc}/{gcp_cluster}/details?project={gcp_project}"
            if datacentre_loc
            else None
        )
    elif provider == "aws":
        if account == "2i2c":
            cluster_console_url = "https://2i2c.awsapps.com/start#/"
        else:
            cluster_console_url = (
                f"https://{account}.signin.aws.amazon.com/console" if account else None
            )
    elif provider == "azure":
        cluster_console_url = "https://portal.azure.com"

    return cluster_console_url


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


def build_hub_list_entry(
    cluster, hub, grafana_url, provider, datacentre_loc, account, cluster_console_url
):
    return {
        # Fallback to name if display_name isn't available
        "name": hub.get("display_name", "name"),
        "domain": f"[{hub['domain']}](https://{hub['domain']})",
        "id": hub["name"],
        "hub_type": hub["helm_chart"],
        "grafana": grafana_url,
        "cluster": cluster["name"],
        "provider": provider,
        "data center location": datacentre_loc,  # Americanising for you ;)
        "UI console link": f"[Use with **{account}** account]({cluster_console_url})"
        if cluster_console_url
        else None,
        "admin_url": f"[admin](https://{hub['domain']}/hub/admin)",
    }


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


def build_hub_statistics_df(df):
    # Write some quick statistics for display
    # Calculate total number of community hubs by removing staging and demo hubs
    # Remove `staging` hubs to count the total number of communites we serve
    filter_out = ["staging", "demo"]
    community_hubs = df.loc[
        df["name"].map(lambda a: all(ii not in a.lower() for ii in filter_out))
    ]
    community_hubs_by_cluster = (
        community_hubs.groupby(["provider", "cluster"])
        .agg({"name": "count"})
        .rename(columns={"name": "count"})
        .sort_values(["provider", "count"], ascending=False)
    )
    community_hubs_by_cluster.loc[("total", ""), "count"] = community_hubs_by_cluster[
        "count"
    ].sum(0)
    community_hubs_by_cluster["count"] = community_hubs_by_cluster["count"].astype(int)

    return community_hubs_by_cluster


def write_df_to_json_and_csv_files(df, file_name_prefix):
    path_table = path_tmp / f"{file_name_prefix}.csv"
    df.to_csv(path_table, index=None)
    df.to_json(path_static / f"{file_name_prefix}.json", orient="index")


def main():
    # Grab the latest list of clusters defined in infrastructure/ explicitly ignoring
    # the test clusters in the ./tests directory
    clusters = [
        filepath
        for filepath in path_clusters.glob("**/*cluster.yaml")
        if "tests/" not in str(filepath) and "templates" not in str(filepath)
    ]

    hub_list = []
    options_list = []
    for cluster_info in clusters:
        cluster_path = cluster_info.parent
        if "schema" in cluster_info.name or "staff" in cluster_info.name:
            continue
        # For each cluster, grab it's YAML w/ the config for each hub
        yaml = cluster_info.read_text()
        cluster = safe_load(yaml)

        # Try to identify the data centre location of the cluster
        # For kubeconfig and Azure providers, this will always default to None since
        # we do not store that information in the cluster.yaml file
        #
        # First try "zone" for GCP clusters
        datacentre_loc = cluster.get(cluster["provider"], {}).get("zone", None)
        if datacentre_loc is None:
            # Try "region" for AWS clusters
            datacentre_loc = cluster.get(cluster["provider"], {}).get("region", None)

        grafana_url = get_cluster_grafana_url(cluster, cluster_path)

        # Define the cloud provider for this cluster which we'll insert into the table below
        # For clusters where we know the provider but can't guess it from the YAML file,
        # we define a few custom mappings.
        custom_providers = {"utoronto": "azure"}
        if cluster["name"] in custom_providers.keys():
            provider = custom_providers[cluster["name"]]
        else:
            provider = cluster["provider"]

        # Don't display anything about Console UI if no info about datacentre available
        cluster_console_url = None

        # We mostly use our 2i2c account to login into cloud provider UI's
        # with a few exceptions
        account = cluster.get("account", "2i2c")

        cluster_console_url = get_cluster_console_url(
            cluster, provider, account, datacentre_loc
        )

        # For each hub in cluster, grab its metadata and add it to the list
        for hub in cluster["hubs"]:
            # Domain can be a list
            if isinstance(hub["domain"], list):
                hub["domain"] = hub["domain"][0]

            hub_values_files = [
                file_name
                for file_name in hub["helm_chart_values_files"]
                if "enc" not in file_name
            ]

            hub_list.append(
                build_hub_list_entry(
                    cluster,
                    hub,
                    grafana_url,
                    provider,
                    datacentre_loc,
                    account,
                    cluster_console_url,
                )
            )

            for config_file in hub_values_files:
                with open(cluster_path.joinpath(config_file)) as f:
                    hub_config = safe_load(f)
                authenticator = get_hub_authentication(cluster_path, hub_config)
                if authenticator:
                    break

            options_list.append(build_options_list_entry(hub, authenticator))

    # Convert to a DataFrame and write it to a CSV file that will be read by Sphinx
    df = pd.DataFrame(hub_list)
    options_df = pd.DataFrame(options_list)
    path_tmp.mkdir(exist_ok=True)

    # Write raw data to CSV and JSON
    write_df_to_json_and_csv_files(df, "hub-table")
    write_df_to_json_and_csv_files(options_df, "hub-options-table")

    community_hubs_by_cluster = build_hub_statistics_df(df)
    write_df_to_json_and_csv_files(community_hubs_by_cluster, "hub-stats")

    print("Finished updating list of hubs table...")


if __name__ == "__main__":
    main()
