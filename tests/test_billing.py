import datetime
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from pandera import Check, Column, DataFrameSchema, DateTime, Float, Index, String
from ruamel.yaml import YAML

from deployer.billing import importers

yaml = YAML(typ="safe", pure=True)


@pytest.fixture
def cluster():
    test_cluster = """
    name: billing-test
    provider: gcp
    gcp:
        project: billing-test
        cluster: billing-test-cluster
        zone: us-central1
        billing:
            paid_by_us: true
            bigquery:
                project: two-eye-two-see
                dataset: cloud_costs
                billing_id: 00DEAD-BEEF000-012345
    """

    c = yaml.load(test_cluster)
    return c


@pytest.fixture
def shared_cluster(cluster):
    cluster["tenancy"] = "shared"
    return cluster


@pytest.fixture
def schema():
    schema = DataFrameSchema(
        {
            "project": Column(String),
            "total_with_credits": Column(Float, Check(lambda x: x > 0.0), coerce=True),
        },
        index=Index(DateTime, name="month"),
    )
    return schema


@pytest.fixture
def start_date():
    return datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)


@pytest.fixture
def end_date():
    return datetime.datetime(2023, 2, 1, tzinfo=datetime.timezone.utc)


def test_gcp_query_builder_invalid_service(cluster):
    with pytest.raises(AssertionError):
        importers.build_gcp_query(cluster, service_id="not-a-service-id")


def test_gcp_query_builder_invalid_billing_project(cluster):
    cluster["gcp"]["billing"]["bigquery"]["project"] = "$%!?"
    with pytest.raises(AssertionError):
        importers.build_gcp_query(cluster)


def test_cost_schema(cluster, schema, start_date, end_date, mocker):
    mocker.patch("google.cloud.bigquery.Client", autospec=True)
    bq_importer = importers.BigqueryGCPBillingCostImporter(cluster)
    bq_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                "month": ["202301"],
                "project": ["test-cluster"],
                "total_with_credits": [42.0],
            }
        )
    )
    schema.validate(bq_importer.get_costs(start_date, end_date))


def test_shared_cluster_importer_single_hub(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {'{namespace="hub1"}': np.repeat(4.0, 31)},
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )

    rows = shared_importer.get_utilization(start_date, end_date)

    assert (
        rows["hub1"].item() == 1.0
    ), "Single hub in shared cluster utilization should be 1.0"


def test_shared_cluster_importer_no_support(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {'{namespace="hub1"}': np.repeat(1.0, 31)},
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )

    rows = shared_importer.get_utilization(start_date, end_date)

    assert (
        rows["support_combined"].item() == 0.0
    ), "Shared cluster without support should have zero combined support utilization"


def test_shared_cluster_importer_multiple_hub(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                '{namespace="hub1"}': np.repeat(1.0, 31),
                '{namespace="hub2"}': np.repeat(9.0, 31),
            },
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )

    rows = shared_importer.get_utilization(start_date, end_date)

    assert (
        rows["hub1"].item() == 0.1
    ), "Shared cluster hub1 should have utilization of 0.1"
    assert (
        rows["hub2"].item() == 0.9
    ), "Shared cluster hub2 should have utilization of 0.9"


def test_shard_cluster_hub_and_support(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                '{namespace="hub1"}': np.repeat(9.9, 31),
                '{namespace="kube-system"}': np.repeat(0.1, 31),
            },
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )

    rows = shared_importer.get_utilization(start_date, end_date)

    assert rows["hub1"].item() == pytest.approx(0.99)
    assert rows["support_combined"].item() == pytest.approx(0.01)


def test_shared_cluster_aggregates_support(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                '{namespace="support"}': np.repeat(9.9, 31),
                '{namespace="kube-system"}': np.repeat(0.1, 31),
            },
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )
    rows = shared_importer.get_utilization(start_date, end_date)
    # Support only is 100% utilization
    assert rows["support_combined"].item() == pytest.approx(
        1.0
    ), "Utilization for support_combined should be the sum of support and kube-system and 1.0"
    assert (
        "support" not in rows
    ), "Utilization for support_combined should replace support"
    assert "kube-system" not in rows


def test_shared_cluster_internal(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                '{namespace="staging"}': np.repeat(75, 31),
                '{namespace="kube-system"}': np.repeat(25, 31),
            },
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )
    rows = shared_importer.get_utilization(start_date, end_date)
    assert rows["2i2c_costs"].item() == pytest.approx(
        0.75
    ), "Utilization for 2i2c_costs should be 0.75"
    assert (
        "staging" not in rows
    ), "Utilization for 2i2c_costs should replace interal namespaces"


def test_shared_cluster_aggregates_internal(shared_cluster, start_date, end_date):
    shared_importer = importers.PrometheusUtilizationImporter(shared_cluster)
    shared_importer._run_query = MagicMock(
        return_value=pd.DataFrame(
            {
                '{namespace="staging"}': np.repeat(25, 31),
                '{namespace="demo"}': np.repeat(50, 31),
                '{namespace="kube-system"}': np.repeat(25, 31),
            },
            index=pd.date_range(start="2023-01-01", end="2023-01-31", freq="D"),
        )
    )
    rows = shared_importer.get_utilization(start_date, end_date)
    assert rows["2i2c_costs"].item() == pytest.approx(
        0.75
    ), "Utilization for 2i2c_costs should be summed over internal namespace"
