"""Pull latest list of hubs features and save as a CSV table.

This is used in two places:

- docs/_static/hub-options-table.json is published with the docs and meant for reuse in other parts of 2i2c
- docs/tmp/hub-options-table.csv is read by reference/options.md to create a list of hubs
"""

import hcl2
import pandas as pd
from utils import (
    get_cluster_provider,
    get_clusters_list,
    path_terraform,
    write_to_json_and_csv_files,
)
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
        return {}


def parse_yaml_config_value_files_for_features(cluster_path, hub_values_files):
    features = {}
    for config_file in hub_values_files:
        with open(cluster_path.joinpath(config_file)) as f:
            hub_config = safe_load(f)
        jupyterhub_config = retrieve_jupyterhub_config_dict(hub_config)

        if jupyterhub_config:
            if not features.get("authenticator", ""):
                features["authenticator"] = get_hub_authentication(jupyterhub_config)
            if not features.get("anonymization", None):
                features["anonymization"] = get_user_anonymization_feature_status(
                    jupyterhub_config
                )
            if not features.get("allusers", None):
                features["allusers"] = get_allusers_feature_status(jupyterhub_config)
            if not features.get("custom_homepage", None):
                features["custom_homepage"] = get_custom_homepage_feature_status(
                    jupyterhub_config
                )
            if not features.get("dedicated_nodepool", None):
                features["dedicated_nodepool"] = get_dedicated_nodepool_status(
                    jupyterhub_config
                )
            if not features.get("gh_scoped_creds", None):
                features["gh_scoped_creds"] = get_gh_scoped_creds(jupyterhub_config)
            if not features.get("custom_html", None):
                features["custom_html"] = get_custom_pages_html(jupyterhub_config)

    return features


def get_cluster_terraform_config(provider, cluster_name):
    """
    Return the configuration dict from the terraform file specific to this cluster_name
    """

    # We're still using the old name for the 2i2c cluster's terraform
    tfvars_file_name = "pilot-hubs" if cluster_name == "2i2c" else cluster_name

    terraform_file = (
        path_terraform / provider / "projects" / f"{tfvars_file_name}.tfvars"
    )

    with open(terraform_file) as f:
        return hcl2.load(f)


def parse_terraform_value_files_for_features(terraform_config):
    features = {}
    # Checks whether or not the cluster has any form of user buckets setup
    if terraform_config.get("user_buckets", False):
        # Then we check which hubs have buckets enabled
        hub_cloud_permissions = terraform_config.get("hub_cloud_permissions", None)
        if hub_cloud_permissions:
            for hub_slug, permissions in hub_cloud_permissions.items():
                # The permission object doesn't have the same structure in AWS
                # as for GCP currently, and requestor_pays is only available for
                # GCP currently. The logic below works, but needs an update if
                # GCP aligns with the same structure as AWS, or if
                # requestor_pays config is added for AWS.
                features[hub_slug] = {
                    "user_buckets": True,
                    "requestor_pays": permissions.get("requestor_pays", False),
                }

    return features


def build_options_list_entry(hub, hub_count, values_files_features, terraform_features):
    domain = f"[{hub['domain']}](https://{hub['domain']})"
    return {
        "domain": domain,
        "dedicated cluster": False if hub_count else True,
        "dedicated nodepool": values_files_features.get("dedicated_nodepool", False),
        "user buckets (scratch/persistent)": terraform_features.get(
            hub["name"], {}
        ).get("user_buckets", False),
        "requester pays for buckets storage": terraform_features.get(
            hub["name"], {}
        ).get("requestor_pays", False),
        "authenticator": values_files_features.get("authenticator", None),
        "user anonymisation": values_files_features.get("anonymization", False),
        "admin access to allusers dirs": values_files_features.get("allusers", False),
        "community domain": False if "2i2c.cloud" in domain else True,
        "custom login page": values_files_features.get("custom_homepage", False),
        "custom html pages": values_files_features.get("custom_html", False),
        "gh-scoped-creds": values_files_features.get("gh_scoped_creds", False),
        #         "static web pages":
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

        # Parse the cluster's terraform config for features and save them in a dict
        provider = get_cluster_provider(cluster)
        terraform_config = get_cluster_terraform_config(provider, cluster["name"])
        terraform_features = parse_terraform_value_files_for_features(terraform_config)

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

            yaml_features = parse_yaml_config_value_files_for_features(
                cluster_path, hub_values_files
            )

            options_list.append(
                build_options_list_entry(
                    hub, prod_hub_count, yaml_features, terraform_features
                )
            )

    # Write raw data to CSV and JSON
    df = pd.DataFrame(options_list)
    df.set_index("domain", inplace=True)
    write_to_json_and_csv_files(df, "hub-options-table")
    print("Finished updating list of hubs features table...")


if __name__ == "__main__":
    main()
