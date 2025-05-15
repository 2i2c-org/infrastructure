import os
import subprocess
from contextlib import ExitStack
from pathlib import Path

from ruamel.yaml import YAML

from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
    find_absolute_path_to_cluster_file,
    get_decrypted_file,
    get_decrypted_files,
)
from deployer.utils.helm import wait_for_deployments_daemonsets
from deployer.utils.rendering import print_colour

from ..utils.jsonnet import render_jsonnet

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


class Hub:
    """
    A single, deployable JupyterHub
    """

    def __init__(self, cluster, spec):
        self.cluster = cluster
        self.spec = spec

    def deploy(self, dask_gateway_version, debug, dry_run):
        """
        Deploy this hub
        """
        # Support overriding domain configuration in the loaded cluster.yaml via
        # a cluster.yaml specified enc-<something>.secret.yaml file that only
        # includes the domain configuration of a typical cluster.yaml file.
        #
        # Check if this hub has an override file. If yes, apply override.
        #
        # FIXME: This could could be generalized so that the cluster.yaml would allow
        #        any of this configuration to be specified in a secret file instead of a
        #        publicly readable file. We should not keep adding specific config overrides
        #        if such need occur but instead make cluster.yaml be able to link to
        #        additional secret configuration.
        if "domain_override_file" in self.spec.keys():
            domain_override_file = self.spec["domain_override_file"]

            with get_decrypted_file(
                self.cluster.config_path.joinpath(domain_override_file)
            ) as decrypted_path:
                with open(decrypted_path) as f:
                    domain_override_config = yaml.load(f)

            self.spec["domain"] = domain_override_config["domain"]

        config_file_path = find_absolute_path_to_cluster_file(self.cluster.config_path)
        for values_file in self.spec["helm_chart_values_files"]:
            if "secret" not in os.path.basename(
                values_file
            ) and not values_file.endswith(".jsonnet"):
                values_file = config_file_path.parent.joinpath(values_file)
                config = yaml.load(values_file)
                # Check if there's config that enables dask-gateway
                dask_gateway_enabled = config.get("dask-gateway", {}).get(
                    "enabled", False
                )
                if dask_gateway_enabled:
                    break

        if dask_gateway_enabled:
            # Install CRDs for daskhub before deployment
            manifest_urls = [
                f"https://raw.githubusercontent.com/dask/dask-gateway/{dask_gateway_version}/resources/helm/dask-gateway/crds/daskclusters.yaml",
                f"https://raw.githubusercontent.com/dask/dask-gateway/{dask_gateway_version}/resources/helm/dask-gateway/crds/traefik.yaml",
            ]

            for manifest_url in manifest_urls:
                subprocess.check_call(["kubectl", "apply", "-f", manifest_url])

        with get_decrypted_files(
            self.cluster.config_path.joinpath(p)
            for p in self.spec["helm_chart_values_files"]
        ) as values_files, ExitStack() as jsonnet_stack:

            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                f"--namespace={self.spec['name']}",
                self.spec["name"],
                HELM_CHARTS_DIR.joinpath(self.spec["helm_chart"]),
            ]

            if dry_run:
                cmd.append("--dry-run")

            if debug:
                cmd.append("--debug")

            # Add on the values files
            for values_file in values_files:
                _, ext = os.path.splitext(values_file)
                if ext == ".jsonnet":
                    rendered_path = jsonnet_stack.enter_context(
                        render_jsonnet(
                            Path(values_file),
                            self.cluster.spec["name"],
                            self.spec["name"],
                        )
                    )
                    cmd.append(f"--values={rendered_path}")
                else:
                    cmd.append(f"--values={values_file}")

            # join method will fail on the PosixPath element if not transformed
            # into a string first
            print_colour(f"Running {' '.join([str(c) for c in cmd])}")
            subprocess.check_call(cmd)

        if not dry_run:
            wait_for_deployments_daemonsets(self.spec["name"])
