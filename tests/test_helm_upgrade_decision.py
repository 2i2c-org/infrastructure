import os
from pathlib import Path
from unittest import TestCase, mock

from ruamel.yaml import YAML

from deployer.commands.generate.helm_upgrade.decision import (
    assign_staging_jobs_for_missing_clusters,
    discover_modified_common_files,
    ensure_support_staging_jobs_have_correct_keys,
    generate_hub_matrix_jobs,
    generate_support_matrix_jobs,
    move_staging_hubs_to_staging_matrix,
)
from deployer.utils.file_acquisition import get_all_cluster_yaml_files

yaml = YAML(typ="safe", pure=True)
case = TestCase()
root_path = Path(__file__).parent.parent


def test_get_all_cluster_yaml_files():
    clusters_path = root_path.joinpath("tests/test-clusters")
    expected_cluster_files = {
        clusters_path.joinpath("cluster1/cluster.yaml"),
        clusters_path.joinpath("cluster2/cluster.yaml"),
    }

    with mock.patch(
        "deployer.utils.file_acquisition.CONFIG_CLUSTERS_PATH", clusters_path
    ):
        result_cluster_files = get_all_cluster_yaml_files()

    assert result_cluster_files == expected_cluster_files
    assert isinstance(result_cluster_files, set)


def test_generate_hub_matrix_jobs_one_hub():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "",
    }

    modified_file = {
        root_path.joinpath("tests/test-clusters/cluster1/hub1.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified: hub1.values.yaml",
        }
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        cluster_file, cluster_config, cluster_info, modified_file
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)


def test_generate_hub_matrix_jobs_many_hubs():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "",
    }

    modified_files = {
        root_path.joinpath("tests/test-clusters/cluster1/hub1.values.yaml"),
        root_path.joinpath("tests/test-clusters/cluster1/hub2.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
            "reason_for_redeploy": "Following helm chart values files were modified: hub1.values.yaml",
        },
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub2",
            "reason_for_redeploy": "Following helm chart values files were modified: hub2.values.yaml",
        },
    ]

    result_matrix_jobs = generate_hub_matrix_jobs(
        cluster_file,
        cluster_config,
        cluster_info,
        modified_files,
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)


def test_generate_hub_matrix_jobs_all_hubs():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "cluster.yaml file was modified",
    }

    reasons = [
        "cluster.yaml file was modified",
        "Core infrastructure has been modified",
        "Core infrastructure has been modified",
    ]
    bool_options = [(True, False), (False, True), (True, True)]

    for reason, bool_option in zip(reasons, bool_options):
        expected_matrix_jobs = [
            {
                "provider": "gcp",
                "cluster_name": "cluster1",
                "hub_name": "staging",
                "reason_for_redeploy": reason,
            },
            {
                "provider": "gcp",
                "cluster_name": "cluster1",
                "hub_name": "hub1",
                "reason_for_redeploy": reason,
            },
            {
                "provider": "gcp",
                "cluster_name": "cluster1",
                "hub_name": "hub2",
                "reason_for_redeploy": reason,
            },
            {
                "provider": "gcp",
                "cluster_name": "cluster1",
                "hub_name": "hub3",
                "reason_for_redeploy": reason,
            },
        ]

        result_matrix_jobs = generate_hub_matrix_jobs(
            cluster_file,
            cluster_config,
            cluster_info,
            set(),
            upgrade_all_hubs_on_this_cluster=bool_option[0],
            upgrade_all_hubs_on_all_clusters=bool_option[1],
        )

        case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
        assert isinstance(result_matrix_jobs, list)
        assert isinstance(result_matrix_jobs[0], dict)


def test_generate_hub_matrix_jobs_skip_deploy_label():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "",
    }

    modified_file = {
        root_path.joinpath("tests/test-clusters/cluster1/hub1.values.yaml"),
    }

    pr_labels = ["unrelated1", "deployer:skip-deploy", "unrelated2"]

    expected_matrix_jobs = []

    result_matrix_jobs = generate_hub_matrix_jobs(
        cluster_file, cluster_config, cluster_info, modified_file, pr_labels
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)


def test_generate_support_matrix_jobs_one_cluster():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "",
    }

    modified_file = {
        root_path.joinpath("tests/test-clusters/cluster1/support.values.yaml"),
    }

    expected_matrix_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "upgrade_support": True,
            "reason_for_support_redeploy": "Following helm chart values files were modified: support.values.yaml",
        }
    ]

    result_matrix_jobs = generate_support_matrix_jobs(
        cluster_file, cluster_config, cluster_info, modified_file
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
    assert isinstance(result_matrix_jobs, list)
    assert isinstance(result_matrix_jobs[0], dict)


def test_generate_support_matrix_jobs_all_clusters():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "cluster.yaml file was modified",
    }

    reasons = [
        "cluster.yaml file was modified",
        "Support helm chart has been modified",
        "Support helm chart has been modified",
    ]
    bool_options = [(True, False), (False, True), (True, True)]

    for reason, bool_option in zip(reasons, bool_options):
        expected_matrix_jobs = [
            {
                "provider": "gcp",
                "cluster_name": "cluster1",
                "upgrade_support": True,
                "reason_for_support_redeploy": reason,
            }
        ]

        result_matrix_jobs = generate_support_matrix_jobs(
            cluster_file,
            cluster_config,
            cluster_info.copy(),
            set(),
            upgrade_support_on_this_cluster=bool_option[0],
            upgrade_support_on_all_clusters=bool_option[1],
        )

        case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)
        assert isinstance(result_matrix_jobs, list)
        assert isinstance(result_matrix_jobs[0], dict)


def test_generate_support_matrix_jobs_skip_deploy_label():
    cluster_file = root_path.joinpath("tests/test-clusters/cluster1/cluster.yaml")
    with open(cluster_file) as f:
        cluster_config = yaml.load(f)

    cluster_info = {
        "cluster_name": cluster_config.get("name", {}),
        "provider": cluster_config.get("provider", {}),
        "reason_for_redeploy": "",
    }

    modified_file = {
        root_path.joinpath("tests/test-clusters/cluster1/support.values.yaml"),
    }

    pr_labels = ["unrelated1", "deployer:skip-deploy", "unrelated2"]

    expected_matrix_jobs = []

    result_matrix_jobs = generate_support_matrix_jobs(
        cluster_file, cluster_config, cluster_info, modified_file, pr_labels
    )

    case.assertCountEqual(result_matrix_jobs, expected_matrix_jobs)


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
    modified_files = [os.path.join("helm-charts", "support", "Chart.yaml")]

    upgrade_all_clusters, upgrade_all_hubs = discover_modified_common_files(
        modified_files
    )

    assert upgrade_all_clusters
    assert not upgrade_all_hubs


def test_move_staging_hubs_to_staging_matrix_job_exists():
    input_hub_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "staging",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "hub1",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
    ]
    input_support_staging_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": True,
            "reason_for_support_redeploy": "cluster.yaml file was modified",
        }
    ]

    expected_hub_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "hub1",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
    ]
    expected_support_staging_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": True,
            "reason_for_support_redeploy": "cluster.yaml file was modified",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "cluster.yaml file was modified",
        }
    ]

    (
        result_hub_matrix_jobs,
        result_support_staging_matrix_jobs,
    ) = move_staging_hubs_to_staging_matrix(
        input_hub_matrix_jobs, input_support_staging_matrix_jobs
    )

    case.assertCountEqual(result_hub_matrix_jobs, expected_hub_matrix_jobs)
    case.assertCountEqual(
        result_support_staging_matrix_jobs, expected_support_staging_matrix_jobs
    )


def test_move_staging_hubs_to_staging_matrix_job_does_not_exist():
    input_hub_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "staging",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "hub1",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
    ]
    input_support_staging_matrix_jobs = []

    expected_hub_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "hub1",
            "reason_for_redeploy": "cluster.yaml file was modified",
        },
    ]
    expected_support_staging_matrix_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": False,
            "reason_for_support_redeploy": "",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "cluster.yaml file was modified",
        }
    ]

    (
        result_hub_matrix_jobs,
        result_support_staging_matrix_jobs,
    ) = move_staging_hubs_to_staging_matrix(
        input_hub_matrix_jobs, input_support_staging_matrix_jobs
    )

    case.assertCountEqual(result_hub_matrix_jobs, expected_hub_matrix_jobs)
    case.assertCountEqual(
        result_support_staging_matrix_jobs, expected_support_staging_matrix_jobs
    )


def test_ensure_support_staging_jobs_have_correct_keys_hubs_exist():
    input_support_staging_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": False,
            "reason_for_support_upgrade": "",
        }
    ]

    input_hub_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "hub_name": "hub1",
            "reason_for_redeploy": "",
        }
    ]

    expected_support_staging_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": False,
            "reason_for_support_upgrade": "",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "Following prod hubs require redeploy: hub1",
        }
    ]

    result_support_staging_jobs = ensure_support_staging_jobs_have_correct_keys(
        input_support_staging_jobs, input_hub_jobs
    )

    case.assertCountEqual(result_support_staging_jobs, expected_support_staging_jobs)


def test_ensure_support_staging_jobs_have_correct_keys_hubs_dont_exist():
    input_support_staging_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": False,
            "reason_for_support_upgrade": "",
        }
    ]

    expected_support_staging_jobs = [
        {
            "cluster_name": "cluster1",
            "provider": "gcp",
            "upgrade_support": False,
            "reason_for_support_upgrade": "",
            "upgrade_staging": False,
            "reason_for_staging_redeploy": "",
        }
    ]

    result_support_staging_jobs = ensure_support_staging_jobs_have_correct_keys(
        input_support_staging_jobs, []
    )

    case.assertCountEqual(result_support_staging_jobs, expected_support_staging_jobs)


def test_assign_staging_jobs_for_missing_clusters_is_missing():
    input_prod_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
        },
    ]

    expected_support_staging_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "upgrade_support": False,
            "reason_for_support_redeploy": "",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "Following prod hubs require redeploy: hub1",
        }
    ]

    result_support_staging_jobs = assign_staging_jobs_for_missing_clusters(
        [], input_prod_jobs
    )

    case.assertCountEqual(result_support_staging_jobs, expected_support_staging_jobs)


def test_assign_staging_jobs_for_missing_clusters_is_present():
    input_prod_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "hub_name": "hub1",
        },
    ]

    input_support_staging_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "upgrade_support": False,
            "reason_for_support_redeploy": "",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "Following prod hubs require redeploy: hub1",
        }
    ]

    expected_support_staging_jobs = [
        {
            "provider": "gcp",
            "cluster_name": "cluster1",
            "upgrade_support": False,
            "reason_for_support_redeploy": "",
            "upgrade_staging": True,
            "reason_for_staging_redeploy": "Following prod hubs require redeploy: hub1",
        }
    ]

    result_support_staging_jobs = assign_staging_jobs_for_missing_clusters(
        input_support_staging_jobs, input_prod_jobs
    )

    case.assertCountEqual(result_support_staging_jobs, expected_support_staging_jobs)
