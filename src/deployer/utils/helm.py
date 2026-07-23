from subprocess import check_call, check_output

from .rendering import print_colour


def wait_for_deployments_daemonsets(name: str):
    """
    Wait for all deployments and daemonsets to be fully rolled out
    """
    print_colour(
        f"Waiting for all deployments and daemonsets in {name} to be ready", "green"
    )
    deployments_and_daemonsets = (
        check_output(
            [
                "kubectl",
                "get",
                f"--namespace={name}",
                "--output=name",
                "deployments,daemonsets",
            ],
        )
        .strip()
        .split()
    )

    for d in deployments_and_daemonsets:
        check_call(
            [
                "kubectl",
                "rollout",
                "status",
                f"--namespace={name}",
                "--timeout=10m",
                "--watch",
                d,
            ],
        )
