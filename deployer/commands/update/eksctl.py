import typer

from deployer.cli_app import update_app
from deployer.commands.generate.dedicated_cluster.aws import generate_eksctl
from deployer.infra_components.cluster import Cluster
from deployer.utils.rendering import print_colour


@update_app.command()
def eksctl(
    cluster_name: str = typer.Argument(
        ..., help="Name of the cluster to update its eksctl config"
    ),
    gpu_hubs: str = typer.Option(
        "",
        prompt="The list of hubs that will be have a gpu",
    ),
):
    """
    Update the eksctl config file for an existing cluster based on the template file
    """
    # These are the variables needed by the templates used to generate the support files
    cluster = Cluster.from_name(cluster_name)
    provider = cluster.spec["provider"]
    if provider != "aws":
        print_colour(
            f"Cluster {cluster_name} is not an AWS cluster, cannot update eksctl config",
            "red",
        )
        exit(1)
    print_colour("Updating the eksctl jsonnet file...", "yellow")
    hubs = []
    dask_hubs = []
    for hub in cluster.hubs:
        hubs.append(hub.spec["name"])
        if hub.type == "daskhub":
            dask_hubs.append(hub.spec["name"])
    vars = {
        "dask_nodes": True if dask_hubs else False,
        "dask_hubs": dask_hubs,
        "cluster_name": cluster_name,
        "cluster_region": cluster.spec["aws"]["region"],
        "hubs": hubs,
        "gpu_nodes": True if gpu_hubs else False,
        "gpu_hubs": gpu_hubs.replace(",", " ").split() if gpu_hubs else [],
    }
    jsonnet_file_path = generate_eksctl(cluster_name, vars)
    print_colour(f"{jsonnet_file_path} Updated")
