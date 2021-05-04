import pytest
from pathlib import Path

def pytest_addoption(parser):
    """
    Define the commandline params that can be passed to pytest.
    """
    parser.addoption(
        "--hub-url",
        action="store"
    )
    parser.addoption(
        "--api-token",
        action="store",
    )
    parser.addoption(
        "--hub-type",
        action="store",
    )


@pytest.fixture
def hub_url(request):
    return request.config.getoption('--hub-url')

@pytest.fixture
def hub_type(request):
    return request.config.getoption('--hub-type')

@pytest.fixture()
def api_token(request):
    return request.config.getoption("--api-token")
