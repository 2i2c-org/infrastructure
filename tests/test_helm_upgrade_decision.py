import os
from pathlib import Path
from unittest import TestCase

from deployer.helm_upgrade_decision import (
    discover_modified_common_files,
    generate_hub_matrix_jobs,
    get_unique_cluster_filepaths,
    generate_support_matrix_jobs,
)

case = TestCase()


def test_get_unique_cluster_filepaths():
    input_filepaths = [
        os.path.join("tests", "test-clusters", "cluster1", "cluster.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "support.values.yaml"),
    ]

    # Expected returns
    expected_cluster_filepaths = [Path("tests/test-clusters/cluster1")]

    result_cluster_filepaths = get_unique_cluster_filepaths(input_filepaths)

    case.assertCountEqual(result_cluster_filepaths, expected_cluster_filepaths)
    assert isinstance(result_cluster_filepaths, list)


def test_generate_hub_matrix_jobs_one_cluster_one_hub():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml")
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub1.values.yaml",
        }
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(input_cluster_filepaths, input_files)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_one_cluster_many_hubs():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "hub2.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub1.values.yaml",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub2",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub2.values.yaml",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(input_cluster_filepaths, input_files)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_one_cluster_all_hubs():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "cluster.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub2",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub3",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(input_cluster_filepaths, input_files)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_many_clusters_one_hub():
    input_cluster_filepaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub1.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub1.values.yaml",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster2/hub1.values.yaml",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(input_cluster_filepaths, input_files)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_many_clusters_many_hubs():
    input_cluster_filepaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "hub2.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub2.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub1.values.yaml",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub2",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/hub2.values.yaml",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster2/hub1.values.yaml",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub2",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster2/hub2.values.yaml",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(input_cluster_filepaths, input_files)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_all_clusters_all_hubs():
    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub2",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub3",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub1",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub2",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "hub_name": "hub3",
            "reason_for_redeploy": "Core infrastructure has changed",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        [],
        set(),
        upgrade_all_hubs_on_all_clusters=True,
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_one_cluster():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "support.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/support.values.yaml",
        }
    ]

    result_matrix_jobs = generate_support_matrix_jobs(
        input_cluster_filepaths, input_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_many_clusters():
    input_cluster_filepaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]
    input_files = {
        os.path.join("tests", "test-clusters", "cluster1", "support.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "support.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster1/support.values.yaml",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "reason_for_redeploy": "Following helm chart values files were modified:\ntests/test-clusters/cluster2/support.values.yaml",
        },
    ]

    result_matrix_jobs = generate_support_matrix_jobs(
        input_cluster_filepaths, input_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_all_clusters():
    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "reason_for_redeploy": "Support helm chart has been modified",
        },
        {
            "provider": "aws",
            "cluster_name": "cluster2",
            "reason_for_redeploy": "Support helm chart has been modified",
        },
    ]

    result_matrix_jobs = generate_support_matrix_jobs(
        [], set(), upgrade_support_on_all_clusters=True
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "reason_for_redeploy" in result_matrix_jobs[0].keys()


def test_discover_modified_common_files_hub_helm_charts():
    input_path_basehub = [os.path.join("helm-charts", "basehub", "Chart.yaml")]
    input_path_daskhub = [os.path.join("helm-charts", "daskhub", "Chart.yaml")]

    (
        basehub_upgrade_all_clusters,
        basehub_upgrade_all_hubs,
    ) = discover_modified_common_files(input_path_basehub)
    (
        daskhub_upgrade_all_clusters,
        daskhub_upgrade_all_hubs,
    ) = discover_modified_common_files(input_path_daskhub)

    assert not basehub_upgrade_all_clusters
    assert basehub_upgrade_all_hubs
    assert not daskhub_upgrade_all_clusters
    assert daskhub_upgrade_all_hubs


def test_discover_modified_common_files_support_helm_chart():
    input_path = [os.path.join("helm-charts", "support", "Chart.yaml")]

    upgrade_all_clusters, upgrade_all_hubs = discover_modified_common_files(input_path)

    assert upgrade_all_clusters
    assert not upgrade_all_hubs
