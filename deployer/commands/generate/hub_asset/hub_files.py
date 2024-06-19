from typing import List

import jinja2
import typer

from deployer.utils.file_acquisition import REPO_ROOT_PATH

from .hub_asset_app import hub_asset_app


@hub_asset_app.command()
def common_values_file(
    provider: str = typer.Option(
        ..., prompt="The provider hosting the cluster: gcp/aws"
    ),
    cluster_name: str = typer.Option(
        ..., prompt="The name of the cluster where the hub will live"
    ),
    authenticator: str = typer.Option(
        ..., prompt="The authenticator type: github/cilogon/auth0/generic"
    ),
    logo_url: str = typer.Option(
        ...,
        prompt="The url of the splash image to be used on the login page of the hub",
    ),
    url: str = typer.Option(..., prompt="The url of the community's homepage"),
    server_ip: str = typer.Option(..., prompt="The server IP"),
    funded_by_name: str = typer.Option(
        ..., prompt="The name of the entity funding the hubs"
    ),
    funded_by_url: str = typer.Option(
        ..., prompt="The url to the website of the entity funding the hubs"
    ),
    admin_users: List[str] = typer.Option([], prompt="The list of hub admin users"),
):
    """
    Outputs the relevant common.values.yaml hub file contents that the engineer can then manually copy-paste into the relevant values.yaml file.
    """

    vars = {
        "provider": provider,
        "cluster_name": cluster_name,
        "authenticator": authenticator,
        "logo_url": logo_url,
        "url": url,
        "server_ip": server_ip,
        "funded_by_name": funded_by_name,
        "funded_by_url": funded_by_url,
        "admin_users": admin_users,
    }

    with open(
        REPO_ROOT_PATH / "config/clusters/templates/common/common-hub.values.yaml"
    ) as f:
        common_hub_values_template = jinja2.Template(f.read())
    print(common_hub_values_template.render(**vars))


@hub_asset_app.command()
def main_values_file(
    provider: str = typer.Option(
        ..., prompt="The provider hosting the cluster: gcp/aws"
    ),
    cluster_name: str = typer.Option(
        ..., prompt="The name of the cluster where the hub will live"
    ),
    hub_name: str = typer.Option(..., prompt="The name of the hub"),
):
    """
    Outputs the relevant hub.values.yaml hub file contents that the engineer can then manually copy-paste into the relevant values.yaml file.
    """

    vars = {
        "provider": provider,
        "cluster_name": cluster_name,
        "hub_name": hub_name,
    }

    with open(REPO_ROOT_PATH / "config/clusters/templates/common/hub.values.yaml") as f:
        hub_values_template = jinja2.Template(f.read())
    print(hub_values_template.render(**vars))


@hub_asset_app.command()
def binderhub_ui_values_file(
    cluster_name: str = typer.Option(
        ..., prompt="Name of the cluster where the hub will live"
    ),
    jupyterhub_domain: str = typer.Option(
        ...,
        prompt="Domain where jupyterhub will run (ex. hub.binder.community.2i2c.cloud)",
    ),
    binderhub_domain: str = typer.Option(
        ...,
        prompt="The domain where binderhub will run (ex. binder.community.2i2c.cloud)",
    ),
    authenticator: str = typer.Option(
        "none",
        prompt="""The authenticator type: github/cilogon/none.
        If none, binderhub will be reachable by anyone and there will be no landing page.
        """,
    ),
    banner_message: str = typer.Option(
        "", prompt="Banner message that will appear in the binderhub UI"
    ),
    about_message: str = typer.Option(
        "", prompt="About message that will appear in the binderhub UI"
    ),
    logo_url: str = typer.Option(
        "",
        prompt="(if authenticated) Splash image url to be used on the login page of the hub",
    ),
    url: str = typer.Option(
        "", prompt="(if authenticated) Url of the community's homepage"
    ),
    funded_by_name: str = typer.Option(
        "", prompt="(if authenticated) Name of the entity funding the hubs"
    ),
    funded_by_url: str = typer.Option(
        "",
        prompt="(if authenticated) Url to the website of the entity funding the hubs",
    ),
):
    """
    Outputs the relevant common.values.yaml hub file contents that the engineer can then manually copy-paste into the relevant values.yaml file.
    """

    vars = {
        "cluster_name": cluster_name,
        "jupyterhub_domain": jupyterhub_domain,
        "binderhub_domain": binderhub_domain,
        "authenticator": authenticator,
        "banner_message": banner_message,
        "about_message": about_message,
        "logo_url": logo_url,
        "url": url,
        "funded_by_name": funded_by_name,
        "funded_by_url": funded_by_url,
    }

    with open(
        REPO_ROOT_PATH / "config/clusters/templates/common/binderhub-ui-hub.values.yaml"
    ) as f:
        common_hub_values_template = jinja2.Template(f.read())
    print(common_hub_values_template.render(**vars))
