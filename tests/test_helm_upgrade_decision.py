import os
from pathlib import Path
from unittest import TestCase

from deployer.helm_upgrade_decision import (
    discover_modified_common_files,
    evaluate_condition_for_upgrading_support_chart,
    generate_hub_matrix_jobs,
    generate_lists_of_filepaths_and_filenames,
    generate_support_matrix_jobs,
)

case = TestCase()


def test_generate_lists_of_filepaths_and_filenames():
    input_filepaths = [
        os.path.join("test-clusters", "cluster1", "cluster.yaml"),
        os.path.join("test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("test-clusters", "cluster1", "support.values.yaml"),
    ]

    # Expected returns
    expected_cluster_filepaths = [Path("test-clusters/cluster1")]
    expected_cluster_files = {
        os.path.join("test-clusters", "cluster1", "cluster.yaml")
    }
    expected_values_files = {
        os.path.join("test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("test-clusters", "cluster1", "support.values.yaml"),
    }
    expected_support_files = {
        os.path.join("test-clusters", "cluster1", "support.values.yaml")
    }

    (
        target_cluster_filepaths,
        target_cluster_files,
        target_values_files,
        target_support_files,
    ) = generate_lists_of_filepaths_and_filenames(input_filepaths)

    case.assertCountEqual(target_cluster_filepaths, expected_cluster_filepaths)
    assert target_cluster_files == expected_cluster_files
    assert target_values_files == expected_values_files
    assert target_support_files == expected_support_files

    assert isinstance(target_cluster_filepaths, list)
    assert isinstance(target_cluster_files, set)
    assert isinstance(target_values_files, set)
    assert isinstance(target_support_files, set)


def test_generate_hub_matrix_jobs_one_cluster_one_hub():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_cluster_files = set()
    input_values_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml")
    }

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"}
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths, input_cluster_files, input_values_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_one_cluster_many_hubs():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_cluster_files = set()
    input_values_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "hub2.values.yaml"),
    }

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub2"},
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths, input_cluster_files, input_values_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_one_cluster_all_hubs():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_cluster_files = {
        os.path.join("tests", "test-clusters", "cluster1", "cluster.yaml")
    }
    input_values_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
    }

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub2"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub3"},
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths, input_cluster_files, input_values_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_many_clusters_one_hub():
    input_cluster_filepaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]
    input_cluster_files = set()
    input_values_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub1.values.yaml"),
    }

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub1"},
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths, input_cluster_files, input_values_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_many_clusters_many_hubs():
    input_cluster_filepaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]
    input_cluster_files = set()
    input_values_files = {
        os.path.join("tests", "test-clusters", "cluster1", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster1", "hub2.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub1.values.yaml"),
        os.path.join("tests", "test-clusters", "cluster2", "hub2.values.yaml"),
    }

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub2"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub1"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub2"},
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths, input_cluster_files, input_values_files
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_hub_matrix_jobs_all_clusters_all_hubs():
    input_cluster_filepaths = [Path("tests/test-clusters/cluster1")]
    input_cluster_files = set()
    input_values_files = {}

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub1"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub2"},
        {"provider": "gcp", "cluster_name": "cluster1", "hub_name": "hub3"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub1"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub2"},
        {"provider": "aws", "cluster_name": "cluster2", "hub_name": "hub3"},
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        input_cluster_filepaths,
        input_cluster_files,
        input_values_files,
        upgrade_all_hubs=True,
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()
    assert "hub_name" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_one_cluster():
    input_dirpaths = [Path("tests/test-clusters/cluster1")]

    expected_matrix_jobs = [{"provider": "gcp", "cluster_name": "cluster1"}]

    result_matrix_jobs = generate_support_matrix_jobs(input_dirpaths)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_many_clusters():
    input_dirpaths = [
        Path("tests/test-clusters/cluster1"),
        Path("tests/test-clusters/cluster2"),
    ]

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1"},
        {"provider": "aws", "cluster_name": "cluster2"},
    ]

    result_matrix_jobs = generate_support_matrix_jobs(input_dirpaths)

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()


def test_generate_support_matrix_jobs_all_clusters():
    input_dirpaths = [Path("tests/test-clusters/cluster1")]

    expected_matrix_jobs = [
        {"provider": "gcp", "cluster_name": "cluster1"},
        {"provider": "aws", "cluster_name": "cluster2"},
    ]

    result_matrix_jobs = generate_support_matrix_jobs(
        input_dirpaths, upgrade_all_clusters=True
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)

    assert "provider" in result_matrix_jobs[0].keys()
    assert "cluster_name" in result_matrix_jobs[0].keys()


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


def test_evaluate_condition_for_upgrading_support_chart():
    input_cluster_files = {
        os.path.join("test-clusters", "cluster1", "cluster.yaml")
    }
    input_support_files = {
        os.path.join("test-clusters", "cluster2", "support.values.yaml")
    }

    expected_dirpaths = [
        Path("test-clusters/cluster1"),
        Path("test-clusters/cluster2"),
    ]

    res_dirpaths = evaluate_condition_for_upgrading_support_chart(
        input_cluster_files, input_support_files
    )

    case.assertCountEqual(res_dirpaths, expected_dirpaths)
