"""Pull latest list of hubs served by infrastructure/ and save as a CSV table."""
from yaml import safe_load
from pathlib import Path
import pandas as pd

path_root = Path(__file__).parent.parent
path_tmp = path_root / "tmp"
path_clusters = path_root / "../config/clusters"

# Grab the latest list of clusters defined in infrastructure/ explicitly ignoring
# the test clusters in the ./tests directory
clusters = [
    filepath
    for filepath in path_clusters.glob("**/*cluster.yaml")
    if "tests/" not in str(filepath)
]

hub_list = []
for cluster_info in clusters:
    cluster_path = cluster_info.parent
    if "schema" in cluster_info.name or "staff" in cluster_info.name:
        continue
    # For each cluster, grab it's YAML w/ the config for each hub
    yaml = cluster_info.read_text()
    cluster = safe_load(yaml)

    # Pull support chart information to populate fields (if it exists)
    support_files = cluster.get("support", {}).get("helm_chart_values_files", None)

    # Incase we don't find any Grafana config, use an empty string as default
    grafana_url = ""

    # Try to identify the data centre location of the cluster
    # For kubeconfig and Azure providers, this will always default to None since
    # we do not store that information in the cluster.yaml file
    #
    # First try "zone" for GCP clusters
    datacentre_loc = cluster.get(cluster["provider"], {}).get("zone", None)
    if datacentre_loc is None:
        # Try "region" for AWS clusters
        datacentre_loc = cluster.get(cluster["provider"], {}).get("region", None)

    # Loop through support files, look for Grafana config, and grab the URL
    if support_files is not None:
        for support_file in support_files:
            with open(cluster_path.joinpath(support_file)) as f:
                support_config = safe_load(f)

            grafana_url = (
                support_config.get("grafana", {}).get("ingress", {}).get("hosts", "")
            )
            # If we find a grafana url, set it here and break the loop, we are done
            if isinstance(grafana_url, list):
                grafana_url = grafana_url[0]
                grafana_url = f"[{grafana_url}](http://{grafana_url})"
                break

    # Track the provider for this cluster for use later
    provider = cluster["provider"] if cluster["provider"] != "kubeconfig" else "azure"

    # For each hub in cluster, grab its metadata and add it to the list
    for hub in cluster["hubs"]:
        # Domain can be a list
        if isinstance(hub["domain"], list):
            hub["domain"] = hub["domain"][0]

        hub_list.append(
            {
                # Fallback to name if display_name isn't available
                "name": hub.get("display_name", "name"),
                "domain": f"[{hub['domain']}](https://{hub['domain']})",
                "id": hub["name"],
                "hub_type": hub["helm_chart"],
                "grafana": grafana_url,
                "cluster": cluster["name"],
                "provider": provider,
                "data center location": datacentre_loc,  # Americanising for you ;)
            }
        )

# Convert to a DataFrame and write it to a CSV file that will be read by Sphinx
df = pd.DataFrame(hub_list)
path_tmp.mkdir(exist_ok=True)

# Write raw data
path_table = path_tmp / "hub-table.csv"
df.to_csv(path_table, index=None)

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

path_stats = path_tmp / "hub-stats.csv"
community_hubs_by_cluster.to_csv(path_stats)
print("Finished updating list of hubs table...")
