import os
import shutil
import subprocess

import typer

from deployer.cli_app import grafana_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.rendering import print_colour


@grafana_app.command()
def deploy_dashboards(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    dashboards_dir: str = typer.Option(
        "dashboards",
        help="""(Optional) ./deploy.py script accepts --dashboards-dir flag, and
             this is the value we provide to that flag.""",
    ),
    dashboard_type: str = typer.Option(
        None,
        help="(Optional) Choose 'jupyterhub' or 'cost' dashboards to deploy. Deploys both types if `None`.",
    ),
):
    """
    Deploy Grafana dashboards to a cluster's Grafana
    instance. This is done via Grafana's REST API, authorized by using a
    previously generated Grafana service account's access token.

    The official JupyterHub dashboards are maintained in
    https://github.com/jupyterhub/grafana-dashboards along with a python script
    to deploy them to Grafana via a REST API.

    The cost monitoring dashboards are maintained in https://github.com/2i2c-org/jupyterhub-cost-monitoring and currently available on AWS clusters only.

    The Grafonnet library needs to be cloned separately, even though jupyterhub/grafana-dashboards includes this as a submodule, because the library also needs to be accessed by 2i2c-org/jupyterhub-cost-monitoring too.
    """
    cluster = Cluster.from_name(cluster_name)
    grafana_url = cluster.get_grafana_url()
    grafana_token = cluster.get_grafana_token()
    cluster_provider = cluster.spec["provider"]
    # Add GRAFANA_TOKEN to the environment variables
    deploy_script_env = os.environ.copy()
    deploy_script_env.update({"GRAFANA_TOKEN": grafana_token})

    allowed_types = [None, "default", "cost"]
    if dashboard_type not in allowed_types:
        raise typer.BadParameter(
            f"Only values {', '.join([str(v) for v in allowed_types])} are allowed."
        )

    if dashboard_type == None or dashboard_type == "cost":
        if cluster_provider != "aws":
            raise Exception(
                f"Cost dashboards are currently available on AWS only. {cluster_name.capitalize()} is deployed on {cluster_provider.upper()}."
            )

    print_colour("Cloning Grafonnet library...")
    subprocess.check_call(
        [
            "git",
            "clone",
            "https://github.com/grafana/grafonnet.git",
            "vendor",
        ]
    )

    print_colour("Cloning jupyterhub/grafana-dashboards...")
    subprocess.check_call(
        [
            "git",
            "clone",
            "https://github.com/jupyterhub/grafana-dashboards",
            "jupyterhub-grafana-dashboards",
        ]
    )

    try:
        if dashboard_type == None or dashboard_type == "default":
            print_colour(
                f"Deploying JupyterHub default dashboards to {cluster_name}..."
            )
            subprocess.check_call(
                ["./deploy.py", grafana_url, f"--dashboards-dir={dashboards_dir}"],
                env=deploy_script_env,
                cwd="jupyterhub-grafana-dashboards",
            )
        if dashboard_type == None or dashboard_type == "cost":
            print_colour(
                f"Deploying cloud cost dashboards to AWS cluster {cluster_name}..."
            )
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "https://github.com/2i2c-org/jupyterhub-cost-monitoring",
                    "jupyterhub-cost-monitoring",
                ]
            )
            subprocess.check_call(
                [
                    "./deploy.py",
                    grafana_url,
                    "--dashboards-dir=../jupyterhub-cost-monitoring/dashboards",
                    "--folder-name=Cloud cost dashboards",
                    "--folder-uid=cloud-cost",
                ],
                env=deploy_script_env,
                cwd="jupyterhub-grafana-dashboards",
            )
            print_colour(f"Done! Cost dashboards deployed to {grafana_url}.")
    finally:
        shutil.rmtree("jupyterhub-grafana-dashboards", ignore_errors=True)
        shutil.rmtree("jupyterhub-cost-monitoring", ignore_errors=True)
        shutil.rmtree("vendor", ignore_errors=True)
