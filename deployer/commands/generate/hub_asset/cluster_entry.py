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
    hub_type: str = typer.Option(..., prompt="The hub type: basehub/daskhub"),
):
    """
    Outputs the relevant cluster.yaml hub entry that the engineer can then manually copy-paste into the relevant cluster.yaml file.
    """

    vars = {
        # Also store the provider, as it's useful for some jinja templates
        # to differentiate between them when rendering the configuration
        "cluster_name": cluster_name,
        "hub_name": hub_name,
        "hub_type": hub_type,
    }

    with open(
        REPO_ROOT_PATH / "config/clusters/templates/common/cluster-entry.yaml"
    ) as f:
        cluster_yaml_template = jinja2.Template(f.read())
    print(cluster_yaml_template.render(**vars))
