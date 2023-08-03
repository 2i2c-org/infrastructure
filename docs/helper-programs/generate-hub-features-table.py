"""Pull latest list of hubs features and save as a CSV table.

This is used in two places:

- docs/_static/hub-options-table.json is published with the docs and meant for re-use in other parts of 2i2c
- docs/tmp/hub-options-table.csv is read by reference/hubs.md to create a list of hubs
"""
import pandas as pd
from utils import get_clusters_list, write_to_json_and_csv_files
from yaml import safe_load


def get_hub_authentication(jupyterhub_config):
    # Return the value of `authenticator_class` from the `hub_config` dictionary
    # and the empty string if none is found
    try:
        return jupyterhub_config["hub"]["config"]["JupyterHub"]["authenticator_class"]
    except KeyError:
        return


def get_user_anonymization_feature_status(jupyterhub_config):
    # Return the value of `anonymizeUsername` from the `hub_config` dictionary
    # and False if none is found
    try:
        return jupyterhub_config["custom"]["auth"]["anonymizeUsername"]
    except KeyError:
        return False


def get_custom_homepage_feature_status(jupyterhub_config):
    try:
        jupyterhub_config["custom"]["homepage"]["gitRepoBranch"]
        return True
    except KeyError:
        return False


def get_allusers_feature_status(jupyterhub_config):
    extra_volume_mounts = []
    try:
        extra_volume_mounts = jupyterhub_config["custom"]["singleuserAdmin"][
            "extraVolumeMounts"
        ]
    except KeyError:
        pass

    for vol in extra_volume_mounts:
        if "allusers" in vol.get("mountPath", ""):
            return True

    return False


def get_dedicated_nodepool_status(jupyterhub_config):
    try:
        jupyterhub_config["singleuser"]["nodeSelector"]["2i2c.org/community"]
        return True
    except KeyError:
        return False


def get_gh_scoped_creds(jupyterhub_config):
    try:
        jupyterhub_config["singleuser"]["extraEnv"]["GH_SCOPED_CREDS_CLIENT_ID"]
        return True
    except KeyError:
        return False


def get_custom_pages_html(jupyterhub_config):
    try:
        extra_files = jupyterhub_config["singleuser"]["extraFiles"]
        for file in extra_files.keys():
            if file.endswith(".html"):
                return True
    except KeyError:
        return False


def build_options_list_entry(
    hub,
    authenticator,
    anonymization,
    allusers,
    custom_homepage,
    hub_count,
    dedicated_nodepool,
    gh_scoped_creds,
    custom_html,
):
    domain = f"[{hub['domain']}](https://{hub['domain']})"
    return {
        "domain": domain,
        "dedicated cluster": False if hub_count else True,
        "dedicated nodepool": dedicated_nodepool,
        "authenticator": authenticator,
        "user anonymisation": anonymization,
        "admin access to allusers dirs": allusers,
        "community domain": False if "2i2c.cloud" in domain else True,
        "custom login page": custom_homepage,
        "custom html pages": custom_html,
        "gh-scoped-creds": gh_scoped_creds,
        #         "static web pages":
        #         "shared cluster":
        #         "buckets":
        #         "dask":
        #         "GPUs":
        #         "profile lists":
    }


def retrieve_jupyterhub_config_dict(hub_config):
    daskhub_type = hub_config.get("basehub", None)
    binderhub_type = hub_config.get("binderhub", None)
    try:
        if daskhub_type:
            return hub_config["basehub"]["jupyterhub"]

        elif binderhub_type:
            return hub_config["binderhub"]["jupyterhub"]
        return hub_config["jupyterhub"]
    except KeyError:
        return


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
        # Also count the hubs per cluster to determine if it's a shared cluster
        prod_hub_count = 0
        for hub in cluster["hubs"]:
            if hub["name"] not in ["staging", "prod"]:
                prod_hub_count += 1

            hub_values_files = [
                file_name
                for file_name in hub["helm_chart_values_files"]
                if "enc" not in file_name
            ]
            authenticator = ""
            anonymization = None
            allusers = None
            custom_homepage = None
            dedicated_nodepool = None
            gh_scoped_creds = None
            custom_html = None
            for config_file in hub_values_files:
                with open(cluster_path.joinpath(config_file)) as f:
                    hub_config = safe_load(f)
                jupyterhub_config = retrieve_jupyterhub_config_dict(hub_config)

                if jupyterhub_config:
                    if not authenticator:
                        authenticator = get_hub_authentication(jupyterhub_config)
                    if not anonymization:
                        anonymization = get_user_anonymization_feature_status(
                            jupyterhub_config
                        )
                    if not allusers:
                        allusers = get_allusers_feature_status(jupyterhub_config)
                    if not custom_homepage:
                        custom_homepage = get_custom_homepage_feature_status(
                            jupyterhub_config
                        )
                    if not dedicated_nodepool:
                        dedicated_nodepool = get_dedicated_nodepool_status(
                            jupyterhub_config
                        )
                    if not gh_scoped_creds:
                        gh_scoped_creds = get_gh_scoped_creds(jupyterhub_config)
                    if not custom_html:
                        custom_html = get_custom_pages_html(jupyterhub_config)

            options_list.append(
                build_options_list_entry(
                    hub,
                    authenticator,
                    anonymization,
                    allusers,
                    custom_homepage,
                    prod_hub_count,
                    dedicated_nodepool,
                    gh_scoped_creds,
                    custom_html,
                )
            )

    # Write raw data to CSV and JSON
    df = pd.DataFrame(options_list)
    df.set_index("domain", inplace=True)
    write_to_json_and_csv_files(df, "hub-options-table")
    print("Finished updating list of hubs features table...")


if __name__ == "__main__":
    main()
