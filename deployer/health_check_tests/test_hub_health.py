import asyncio
import contextlib
from pathlib import Path

import nbformat
from hucl.flows import (
    create_user,
    ensure_api_url,
    start_server,
    stop_server,
)
from jupyter_kernel_client import KernelClient

from deployer.utils.rendering import print_colour


def notebook_dir(hub_type: str) -> Path:
    return Path(__file__).parent.joinpath("test-notebooks", hub_type)


def execute_notebook(path: Path, server_url: str, service_api_token: str):
    """
    Execute a single notebook under a new kernel.
    """
    with path.open() as f:
        nb = nbformat.read(f, as_version=4)

    # Extract non-empty code cell sources from the notebook
    code_fragments = (
        c.source for c in nb.cells if c.cell_type == "code" and c.source.strip()
    )

    # Start a kernel, and run each fragment serially
    with KernelClient(
        server_url=server_url.rstrip("/"), token=service_api_token
    ) as kernel:
        for i, fragment in enumerate(code_fragments, start=1):
            reply = kernel.execute(fragment)

            if reply["execution_count"] != i:
                raise RuntimeError("Cell was not executed")

            if reply["status"] != "ok":
                raise RuntimeError("Execution status was not OK")


@contextlib.asynccontextmanager
async def launch_temporary_deployment_server(hub_url: str, service_api_token: str):
    """
    Spin up a temporary JupyterHub server under the `deployment-service-check` name.
    Stop the server after completion.
    """
    username = "deployment-service-check"

    # First, ensure we have a user
    hub_api_url = ensure_api_url(f"{hub_url}/hub/api")
    await create_user.asyn(
        api_url=hub_api_url, api_token=service_api_token, user_name=username
    )

    # Now spin up a server
    partial_server_url = await start_server.asyn(
        api_url=hub_api_url, api_token=service_api_token, user_name=username
    )
    try:
        yield f"{hub_url}{partial_server_url}"

    finally:
        await stop_server.asyn(
            api_url=hub_api_url,
            api_token=service_api_token,
            user_name=username,
        )


async def test_hub_healthy(hub_url, api_token, hub_type):
    """
    After each hub gets deployed, validate that it 'works'.

    Automatically create a temporary user, start their server and run a test notebook, making
    sure it runs to completion. Stop and delete the test server at the end. If any of these
    steps fail, declare the hub as having failed the health check
    """
    loop = asyncio.get_running_loop()
    notebooks_path = notebook_dir(hub_type)
    print_colour(f"Starting hub {hub_url} health validation...", "yellow")
    try:
        async with launch_temporary_deployment_server(hub_url, api_token) as server_url:
            for notebook_path in notebooks_path.glob("*.ipynb"):
                print_colour(f"Running {notebook_path.name} test notebook...", "yellow")
                await loop.run_in_executor(
                    None, execute_notebook, notebook_path, server_url, api_token
                )
    except Exception as e:
        import traceback

        traceback.print_exception(e)
        print_colour(
            f"Hub {hub_url} not healthy! Stopping further deployments. Exception was {e}.",
            "red",
        )
        raise (e)
    else:
        print_colour(f"Hub {hub_url} is healthy!")
