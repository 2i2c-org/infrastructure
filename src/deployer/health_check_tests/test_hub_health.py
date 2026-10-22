import contextlib
import os
from pathlib import Path

import asyncio
import aiohttp
import difflib
from jhub_client.execute import JupyterHubAPI
from jhub_client.utils import parse_notebook_cells

from deployer.utils.rendering import print_colour


def notebook_dir(hub_type):
    return (Path(__file__).parent).joinpath("test-notebooks", hub_type)


@contextlib.contextmanager
def log_group(title: str):
    if "GITHUB_ACTIONS" not in os.environ:
        print_colour(f"\033[4m❯ {title}\033[0m", "red")
        yield
    else:
        print(f"::group::{{{title}}}")
        yield
        print("::endgroup::")


VERY_LARGE_TIMEOUT = 9999


async def run_notebook_in_default_kernel(
    username: str,
    jupyter,
    cells,
    cleanup_timeout_s: float,
    validate: bool = False,
):
    kernel_id, kernel = await jupyter.ensure_kernel()
    try:
        result_cells = []
        async with kernel:
            for i, (code, expected_result) in enumerate(cells):
                kernel_result = await kernel.send_code(
                    username,
                    code,
                    timeout=VERY_LARGE_TIMEOUT,
                    wait=True,
                )
                result_cells.append((code, kernel_result))
                # logger.debug(
                #    f"kernel executing cell={i} code=\n{textwrap.indent(code, '   >>> ')}"
                # )
                # logger.debug(
                #    f"kernel result cell={i} result=\n{textwrap.indent(kernel_result, '   | ')}"
                # )
                if validate and (kernel_result.strip() != expected_result.strip()):
                    diff = "".join(difflib.unified_diff(kernel_result, expected_result))
                    raise ValueError(
                        f"execution of cell={i} did not match expected result diff={diff}"
                    )
    finally:
        await asyncio.wait_for(
            jupyter.delete_kernel(kernel_id), timeout=cleanup_timeout_s
        )


async def fetch_hub_version(hub_url: str):
    api_url = f"{hub_url.removesuffix('/')}/hub/api"
    async with aiohttp.ClientSession() as session, session.get(api_url) as response:
        data = await response.json()

    return data["version"]


@contextlib.asynccontextmanager
async def using_jupyterhub_token(token: str):
    # Export the hub health check service as an env var so that jhub_client can read it.
    orig_service_token = os.environ.get("JUPYTERHUB_API_TOKEN", None)

    try:
        os.environ["JUPYTERHUB_API_TOKEN"] = token
        yield
    finally:
        if orig_service_token is not None:
            os.environ["JUPYTERHUB_API_TOKEN"] = orig_service_token
        else:
            del os.environ["JUPYTERHUB_API_TOKEN"]


async def ensure_no_pending_user(hub: JupyterHubAPI, username: str):
    if user := (await hub.get_user(username)):
        if user["server"] and not user["pending"]:
            await hub.ensure_server_deleted(username, 60)

        # If we don't delete the user too, than we won't be able to start a kernel for it.
        # This is because we would have lost its api token from the previous run.
        await hub.delete_user(username)


async def test_hub_healthy(
    *,
    hub_url: str,
    api_token: str,
    hub_type: str,
    test_notebooks: bool,
    cleanup_timeout_s: float,
):
    # First, check we can hit the hub

    print_colour(f"Running health checks for {hub_url} ...", "yellow")

    with log_group("Hub health"):
        print_colour("Checking hub API is reachable ...", "yellow")
        hub_version = await fetch_hub_version(hub_url)
        print_colour(f"Found hub running version {hub_version}", "green")

    username = "deployment-service-check"
    async with using_jupyterhub_token(api_token), JupyterHubAPI(hub_url) as hub:
        await ensure_no_pending_user(hub, username)

        # Start a server
        print_colour(f"Starting health-check server for {username}...", "yellow")
        server = await hub.ensure_server(
            username,
            create_user=True,
            timeout=VERY_LARGE_TIMEOUT,
        )
        try:
            async with server:
                with log_group("Server health"):
                    # Check the API
                    print_colour("Checking server API is reachable ...", "yellow")
                    specs = await server.list_kernel_specs()
                    default = specs["default"]
                    print_colour(
                        f"Found default kernelspec {default} for server", "green"
                    )

                    # Run some workflows
                    if test_notebooks:
                        with log_group("Notebook workflow health"):
                            nb_dir = notebook_dir(hub_type)
                            print_colour(
                                "Checking singleuser workflows succeed ...", "yellow"
                            )
                            test_notebook_paths = (
                                os.path.join(root, name)
                                for root, _, files in os.walk(nb_dir, topdown=False)
                                for _, name in enumerate(files)
                            )
                            for test_notebook_path in test_notebook_paths:
                                name = os.path.basename(test_notebook_path)
                                # We only want to run the "scale_dask_workers.ipynb" file if the
                                # check_dask_scaling variable is true. We continue in the loop if
                                # check_dask_scaling == False when we iterate over this file.
                                print_colour(
                                    f"Running {name} test notebook ...", "yellow"
                                )

                                cells = parse_notebook_cells(test_notebook_path)
                                await run_notebook_in_default_kernel(
                                    username,
                                    server,
                                    cells,
                                    validate=False,
                                )
                    else:
                        print_colour("Skipping notebook tests ...", "yellow")

            print_colour(f"Hub {hub_url} is healthy!")
        finally:
            await asyncio.wait_for(
                hub.ensure_server_deleted(username, timeout=VERY_LARGE_TIMEOUT),
                timeout=cleanup_timeout_s,
            )
