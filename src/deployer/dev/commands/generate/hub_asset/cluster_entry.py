import jinja2
import typer

from deployer.utils.file_acquisition import REPO_ROOT_PATH

from .hub_asset_app import hub_asset_app


@hub_asset_app.command()
def cluster_entry(
    cluster_name: str = typer.Option(
        ..., prompt="The name of the cluster where the hub will live"
    ),
    hub_name: str = typer.Option(..., prompt="The name of the hub"),
):
    """
    Outputs the relevant cluster.yaml hub entry that the engineer can then manually copy-paste into the relevant cluster.yaml file.
    """

    vars = {
        "cluster_name": cluster_name,
        "hub_name": hub_name,
    }

    with open(
        REPO_ROOT_PATH / "config/clusters/templates/common/cluster-entry.yaml"
    ) as f:
        cluster_hub_entry_template = jinja2.Template(f.read())
    print(cluster_hub_entry_template.render(**vars))
