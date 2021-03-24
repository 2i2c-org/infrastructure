import os
import pytest


# Can be flaky due to image pull durations, let's re-run it once more if needed
@pytest.mark.asyncio
@pytest.mark.flaky(reruns=1)
async def test_hub_healthy(hub, api_token):
    """
    Tests the hub is healthy.

    Executes some test notebooks on each hub and validates their output.
    """
    hub_name = hub.spec["name"]
    hub_template = hub.spec["template"]

    try:
        print(f"Starting hub {hub_name} health validation...")
        if hub_template == "daskhub":
            test_notebook_dir = os.path.join(os.path.dirname(__file__), 'dask-health-check-notebooks')
        else:
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
