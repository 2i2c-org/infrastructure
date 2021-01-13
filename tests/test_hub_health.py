import os
import pytest

@pytest.mark.asyncio
async def test_hub_healthy(hub, api_token):
    hub_name = hub.spec["name"]
    try:
        print(f"Starting hub {hub_name} health validation...")
        test_notebook_dir = os.path.join(os.path.dirname(__file__), 'health-check-notebooks')
        for root, directories, files in os.walk(test_notebook_dir, topdown=False):
            for name in files:
                print(f"Running {name} test notebook...")
                test_notebook_path = os.path.join(root, name)
                await hub.check_hub_health(test_notebook_path, api_token)
        print(f"Hub {hub_name} is healthy!")
    except Exception as e:
        print(f"Hub {hub_name} not healthy! Stopping further deployments. Exception was {e}.")
        raise(e)
