"""Pull latest list of hubs features and save as a CSV table.

This is used in two places:

- docs/_static/hub-options-table.json is published with the docs and meant for re-use in other parts of 2i2c
- docs/tmp/hub-options-table.csv is read by reference/hubs.md to create a list of hubs
"""
import pandas as pd
from utils import get_clusters_list, write_to_json_and_csv_files
from yaml import safe_load


def get_hub_authentication(hub_config, daskhub_type, binderhub_type):
    # Return the value of `authenticator_class` from the `hub_config` dictionary
    # and the empty string if none is found
    try:
        if daskhub_type:
            return hub_config["basehub"]["jupyterhub"]["hub"]["config"]["JupyterHub"][
                "authenticator_class"
            ]
        elif binderhub_type:
            return hub_config["binderhub"]["jupyterhub"]["hub"]["config"]["JupyterHub"][
                "authenticator_class"
            ]
        return hub_config["jupyterhub"]["hub"]["config"]["JupyterHub"][
            "authenticator_class"
        ]
    except KeyError:
        pass

    return


def get_user_anonymization_feature_status(hub_config, daskhub_type, binderhub_type):
    # Return the value of `anonymizeUsername` from the `hub_config` dictionary
    # and False if none is found
    try:
        if daskhub_type:
            return hub_config["basehub"]["jupyterhub"]["custom"]["auth"][
                "anonymizeUsername"
            ]
        elif binderhub_type:
            return hub_config["binderhub"]["jupyterhub"]["custom"]["auth"][
                "anonymizeUsername"
            ]

        return hub_config["jupyterhub"]["custom"]["auth"]["anonymizeUsername"]
    except KeyError:
        pass

    return False


def get_custom_homepage_feature_status(hub_config, daskhub_type, binderhub_type):
    try:
        if daskhub_type:
            hub_config["basehub"]["jupyterhub"]["custom"]["homepage"]["gitRepoBranch"]
            return True
        elif binderhub_type:
            hub_config["binderhub"]["jupyterhub"]["custom"]["homepage"]["gitRepoBranch"]
            return True

        hub_config["jupyterhub"]["custom"]["homepage"]["gitRepoBranch"]
        return True
    except KeyError:
        return False


def get_allusers_feature_status(hub_config, daskhub_type, binderhub_type):
    extra_volume_mounts = []
    try:
        if daskhub_type:
            extra_volume_mounts = hub_config["basehub"]["jupyterhub"]["custom"][
                "singleuserAdmin"
            ]["extraVolumeMounts"]
        elif binderhub_type:
            extra_volume_mounts = hub_config["binderhub"]["jupyterhub"]["custom"][
                "singleuserAdmin"
            ]["extraVolumeMounts"]

        extra_volume_mounts = hub_config["jupyterhub"]["custom"]["singleuserAdmin"][
            "extraVolumeMounts"
        ]
    except KeyError:
        pass

    for vol in extra_volume_mounts:
        if "allusers" in vol.get("mountPath", ""):
            return True

    return False


def build_options_list_entry(
    hub, authenticator, anonymization, allusers, custom_homepage
):
    domain = f"[{hub['domain']}](https://{hub['domain']})"
    return {
        "domain": domain,
        "authenticator": authenticator,
        "user id anonymisation": anonymization,
        "admin access to all user's home dirs": allusers,
        "community domain": False if "2i2c.cloud" in domain else True,
        "custom login page": custom_homepage,
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

            authenticator = ""
            anonymization = False
            allusers = False
            custom_homepage = False
            for config_file in hub_values_files:
                with open(cluster_path.joinpath(config_file)) as f:
                    hub_config = safe_load(f)

                daskhub_type = hub_config.get("basehub", None)
                binderhub_type = hub_config.get("binderhub", None)

                if not authenticator:
                    authenticator = get_hub_authentication(
                        hub_config, daskhub_type, binderhub_type
                    )
                if not anonymization:
                    anonymization = get_user_anonymization_feature_status(
                        hub_config, daskhub_type, binderhub_type
                    )
                if not allusers:
                    allusers = get_allusers_feature_status(
                        hub_config, daskhub_type, binderhub_type
                    )
                if not custom_homepage:
                    custom_homepage = get_custom_homepage_feature_status(
                        hub_config, daskhub_type, binderhub_type
                    )

            options_list.append(
                build_options_list_entry(
                    hub, authenticator, anonymization, allusers, custom_homepage
                )
            )

    # Write raw data to CSV and JSON
    df = pd.DataFrame(options_list)
    df.set_index("domain", inplace=True)
    write_to_json_and_csv_files(df, "hub-options-table")
    print("Finished updating list of hubs features table...")


if __name__ == "__main__":
    main()
