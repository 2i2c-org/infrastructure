import os
from pathlib import Path

import pytest
from jhub_client.execute import JupyterHubAPI, execute_notebook


@pytest.fixture
def notebook_dir(hub_type):
    return (Path(__file__).parent).joinpath("test-notebooks", hub_type)


async def check_hub_health(hub_url, test_notebook_path, service_api_token):
    """
    After each hub gets deployed, validate that it 'works'.

    Automatically create a temporary user, start their server and run a test notebook, making
    sure it runs to completion. Stop and delete the test server at the end. If any of these
    steps fail, declare the hub as having failed the health check
    """

    username = "deployment-service-check"

    # Export the hub health check service as an env var so that jhub_client can read it.
    orig_service_token = os.environ.get("JUPYTERHUB_API_TOKEN", None)

    try:
        os.environ["JUPYTERHUB_API_TOKEN"] = service_api_token

        # Cleanup: if the server takes more than 90s to start, then because it's in a `spawn pending` state,
        # it cannot be deleted. So we delete it in the next iteration, before starting a new one,
        # so that we don't have more than one running.
        hub = JupyterHubAPI(hub_url)
        async with hub:
            user = await hub.get_user(username)
            if user:
                if user["server"] and not user["pending"]:
                    await hub.ensure_server_deleted(username, 60)

                # If we don't delete the user too, than we won't be able to start a kernel for it.
                # This is because we would have lost its api token from the previous run.
                await hub.delete_user(username)

        # Temporary fix for https://github.com/2i2c-org/infrastructure/issues/2146#issuecomment-1649445203
        # FIXME: Remove this once a fix in kubespawner gets implemented
        user_options = {}
        if "leap" in hub_url:
            user_options = {
                "profile": "medium-full",
                "requests": "mem_8",
                "image": "pangeo",
            }

        # Create a new user, start a server and execute a notebook
        await execute_notebook(
            hub_url,
            test_notebook_path,
            username=username,
            server_creation_timeout=360,
            kernel_execution_timeout=360,  # This doesn't do anything yet
            create_user=True,
            delete_user=False,  # To be able to delete its server in case of failure
            stop_server=True,  # If the health check succeeds, this will delete the server
            validate=False,  # Don't validate notebook outputs. We only care that it runs top-to-bottom without error.
            user_options=user_options,
        )
    finally:
        if orig_service_token:
            os.environ["JUPYTERHUB_API_TOKEN"] = orig_service_token
        else:
            del os.environ["JUPYTERHUB_API_TOKEN"]


@pytest.mark.asyncio
async def test_hub_healthy(hub_url, api_token, notebook_dir, check_dask_scaling):
    try:
        print(f"Starting hub {hub_url} health validation...")
        for root, directories, files in os.walk(notebook_dir, topdown=False):
            for i, name in enumerate(files):
                # We only want to run the "scale_dask_workers.ipynb" file if the
                # check_dask_scaling variable is true. We continue in the loop if
                # check_dask_scaling == False when we iterate over this file.
                if (not check_dask_scaling) and (name == "scale_dask_workers.ipynb"):
                    continue

                print(f"Running {name} test notebook...")
                test_notebook_path = os.path.join(root, name)
                await check_hub_health(hub_url, test_notebook_path, api_token)

        print(f"Hub {hub_url} is healthy!")
    except Exception as e:
        print(
            f"Hub {hub_url} not healthy! Stopping further deployments. Exception was {e}."
        )
        raise (e)
