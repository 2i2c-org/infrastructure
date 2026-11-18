import asyncio
import contextlib
import os
from pathlib import Path

import aiohttp
from hucl.flows import (
    create_user,
    delete_user,
    ensure_api_url,
    start_server,
    stop_server,
)

from deployer.utils.rendering import print_colour


def notebook_dir(hub_type: str) -> Path:
    return (Path(__file__).parent).joinpath("test-notebooks", hub_type)


@contextlib.contextmanager
def log_group(title: str):
    if "GITHUB_ACTIONS" not in os.environ:
        print_colour(f"\033[4m❯ {title}\033[0m", "red")
        yield
    else:
        print(f"::group::{title}")
        yield
        print("::endgroup::")


VERY_LARGE_TIMEOUT = 9999


def bearer_auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_health_check_user(
    session, hub_url: str, service_api_token: str, user_name: str
) -> str:
    """
    Ensure we have a new user, and determine the API token for it
    """

    # First, ensure we have a user
    hub_api_url = ensure_api_url(f"{hub_url}/hub/api")

    # Ensure we have a fresh user
    await delete_user.asyn(
        api_url=hub_api_url, api_token=service_api_token, user_name=user_name
    )
    await create_user.asyn(
        api_url=hub_api_url, api_token=service_api_token, user_name=user_name
    )
    return await create_user_api_token(session, hub_url, service_api_token, user_name)


async def create_user_api_token(
    session: aiohttp.ClientSession, hub_url: str, service_api_token: str, user_name: str
) -> str:
    hub_api_url = ensure_api_url(f"{hub_url}/hub/api")

    async with session.post(
        f"{hub_api_url}/users/{user_name}/tokens",
        headers=bearer_auth_headers(service_api_token),
        json={"note": f"Health check token for {user_name}"},
        raise_for_status=True,
    ) as resp:
        data = await resp.json()
        return data["token"]


@contextlib.asynccontextmanager
async def ensure_health_check_server(
    hub_url: str, user_api_token: str, user_name: str, cleanup_timeout_s: float
):
    """
    Spin up a temporary JupyterHub server under the `deployment-service-check` name.
    Stop the server after completion.
    """
    # First, ensure we have a user
    hub_api_url = ensure_api_url(f"{hub_url}/hub/api")

    try:
        # Now spin up a server
        partial_server_url = (
            await start_server.asyn(
                api_url=hub_api_url, api_token=user_api_token, user_name=user_name
            )
        ).rstrip("/")
        yield f"{hub_url}{partial_server_url}"

    finally:
        await asyncio.wait_for(
            stop_server.asyn(
                api_url=hub_api_url,
                api_token=user_api_token,
                user_name=user_name,
            ),
            timeout=cleanup_timeout_s,
        )


async def fetch_hub_version(session: aiohttp.ClientSession, hub_url: str):
    api_url = ensure_api_url(f"{hub_url}/hub/api")
    async with session.get(api_url) as response:
        data = await response.json()

    return data["version"]


async def fetch_server_default_kernelspec(
    session: aiohttp.ClientSession, server_url: str, user_api_token: str
):
    async with session.get(
        f"{server_url}/api/kernelspecs",
        headers=bearer_auth_headers(user_api_token),
        raise_for_status=True,
    ) as resp:
        specs = await resp.json()
    return specs["default"]


async def test_hub_healthy(
    *,
    hub_url: str,
    api_token: str,
    hub_type: str,
    test_notebooks: bool,
    cleanup_timeout_s: float,
):
    hub_url_base = hub_url.rstrip("/")

    user_name = "deployment-service-check"

    print_colour(f"Running health checks for {hub_url} ...", "yellow")
    async with aiohttp.ClientSession() as session:
        # First, check we can hit the hub
        with log_group("Hub health"):
            print_colour("Checking hub API is reachable ...", "yellow")
            hub_version = await fetch_hub_version(session, hub_url_base)
            print_colour(f"Found hub running version {hub_version}", "green")

        # First, then that we can hit the server
        with log_group("Server health"):
            # Create a user API token. We don't need to do this if the
            # service API token has sufficient privs, but using a user.
            # token lets us test that pathway!
            print_colour("Creating user API token ...", "yellow")
            user_api_token = await create_health_check_user(
                session, hub_url_base, api_token, user_name
            )

            print_colour("Starting server ...", "yellow")
            async with ensure_health_check_server(
                hub_url_base, user_api_token, user_name, cleanup_timeout_s
            ) as server_url_base:
                # Check the API
                print_colour("Checking server API is reachable ...", "yellow")
                default = await fetch_server_default_kernelspec(
                    session, server_url_base, user_api_token
                )
                print_colour(f"Found default kernelspec {default} for server", "green")

                print_colour(f"Hub {hub_url} is healthy!")
