import os
import shutil
import subprocess

import typer

from deployer.cli_app import CONTINUOUS_DEPLOYMENT, app
from deployer.infra_components.cluster import Cluster
from deployer.utils.rendering import print_colour


@app.command(rich_help_panel=CONTINUOUS_DEPLOYMENT)
def deploy_dashboards(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    dashboard_type: str = typer.Option(
        None,
        help="(Optional) Choose 'default' or 'cost' dashboards to deploy. Deploys both types if `None`.",
    ),
    dashboard_dir_default: str = typer.Option(
        "dashboards",
        help="""(Optional) ./deploy.py script accepts manual override for where JupyterHub default dashboards are defined. Path is relative to jupyterhub-grafana-dashboards/deploy.py script.
        
        Warning: you should manually delete dashboards deployed this way, since they are not cleaned up in the CI/CD.        
        """,
    ),
    dashboard_dir_cost: str = typer.Option(
        "../jupyterhub-cost-monitoring/dashboards",
        help="""(Optional) ./deploy.py script accepts manual override where cloud cost dashboards are defined. Path is relative to jupyterhub-grafana-dashboards/deploy.py script.
        
        Warning: you should manually delete dashboards deployed this way, since they are not cleaned up in the CI/CD.
        """,
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

    if dashboard_type == "cost":
        if cluster_provider != "aws":
            print_colour(
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
                [
                    "./deploy.py",
                    grafana_url,
                    f"--dashboards-dir={dashboard_dir_default}",
                ],
                env=deploy_script_env,
                cwd="jupyterhub-grafana-dashboards",
            )
        if dashboard_type == None or dashboard_type == "cost":
            print_colour(
                f"Deploying cloud cost dashboards to AWS cluster {cluster_name}..."
            )
            if dashboard_dir_cost == "../jupyterhub-cost-monitoring/dashboards":
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
                    f"--dashboards-dir={dashboard_dir_cost}",
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
