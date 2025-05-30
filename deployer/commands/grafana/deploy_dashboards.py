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
):
    """
    Deploy the latest official JupyterHub dashboards to a cluster's grafana
    instance. This is done via Grafana's REST API, authorized by using a
    previously generated Grafana service account's access token.

    The official JupyterHub dashboards are maintained in
    https://github.com/jupyterhub/grafana-dashboards along with a python script
    to deploy them to Grafana via a REST API.

    NOTE: 2i2c-hosted dashboards live at https://github.com/2i2c-org/grafana-dashboards while features are waiting to be upstreamed to the official repository.
    """
    cluster = Cluster.from_name(cluster_name)
    grafana_url = cluster.get_grafana_url()
    grafana_token = cluster.get_grafana_token()
    cluster_provider = cluster.spec["provider"]

    print_colour("Cloning jupyterhub/grafana-dashboards...")
    subprocess.check_call(
        [
            "git",
            "clone",
            "https://github.com/2i2c-org/grafana-dashboards",
            "jupyterhub-grafana-dashboards",
        ]
    )

    # Add GRAFANA_TOKEN to the environment variables for
    # jupyterhub/grafana-dashboards' deploy.py script
    deploy_script_env = os.environ.copy()
    deploy_script_env.update({"GRAFANA_TOKEN": grafana_token})

    try:
        print_colour(f"Deploying grafana dashboards to {cluster_name}...")
        subprocess.check_call(
            ["./deploy.py", grafana_url, f"--dashboards-dir={dashboards_dir}"],
            env=deploy_script_env,
            cwd="jupyterhub-grafana-dashboards",
        )

        if cluster_provider == "aws":
            print_colour("Deploying cloud cost dashboards to an AWS cluster...")
            subprocess.check_call(
                [
                    "./deploy.py",
                    grafana_url,
                    "--dashboards-dir=../grafana-dashboards",
                    "--folder-name=Cloud cost dashboards",
                    "--folder-uid=cloud-cost",
                ],
                env=deploy_script_env,
                cwd="jupyterhub-grafana-dashboards",
            )

        print_colour(f"Done! Dashboards deployed to {grafana_url}.")

    finally:
        # Delete the directory where we cloned the repo.
        # The deployer cannot call jsonnet to deploy the dashboards if using a temp directory here.
        # Might be because opening more than once of a temp file is tried
        # (https://docs.python.org/3.8/library/tempfile.html#tempfile.NamedTemporaryFile)
        shutil.rmtree("jupyterhub-grafana-dashboards")
