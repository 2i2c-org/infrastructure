import pytest


def pytest_addoption(parser):
    """
    Define the commandline params that can be passed to pytest.
    """
    parser.addoption("--hub-url", action="store")
    parser.addoption(
        "--api-token",
        action="store",
    )
    parser.addoption(
        "--hub-type",
        action="store",
    )
    parser.addoption(
        "--check-dask-scaling",
        action="store_true",
    )


@pytest.fixture
def hub_url(request):
    return request.config.getoption("--hub-url")


@pytest.fixture
def hub_type(request):
    return request.config.getoption("--hub-type")


@pytest.fixture()
def api_token(request):
    return request.config.getoption("--api-token")


@pytest.fixture()
def check_dask_scaling(request):
    return request.config.getoption("--check-dask-scaling")
