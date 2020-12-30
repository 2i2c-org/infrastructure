import os
import pytest
from pathlib import Path
import sys

from .context import auth
from .context import deploy

@pytest.mark.asyncio
async def test_hub_healthy():
    AUTH0_DOMAIN = '2i2c.us.auth0.com'

    k = auth.KeyProvider(AUTH0_DOMAIN, os.environ['AUTH0_MANAGEMENT_CLIENT_ID'], os.environ['AUTH0_MANAGEMENT_CLIENT_SECRET'])

    PROXY_SECRET_KEY = bytes.fromhex(os.environ['PROXY_SECRET_KEY'])

    config_file_path = Path(__file__).parent / "staging-hubs.yaml"
    print(config_file_path)
    clusters = deploy.parse_clusters(config_file_path)

    for cluster in clusters:
        with cluster.auth():
            for hub in cluster.hubs:
                await hub.deploy(k, PROXY_SECRET_KEY)
