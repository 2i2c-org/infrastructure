from __future__ import annotations

import os
import subprocess
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from deployer.infra_components.cluster import Cluster

from deployer.utils.file_acquisition import (
    HELM_CHARTS_DIR,
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

    def __init__(self, cluster: Cluster, spec):
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
                self.cluster.config_dir / domain_override_file
            ) as decrypted_path:
                with open(decrypted_path) as f:
                    domain_override_config = yaml.load(f)

            self.spec["domain"] = domain_override_config["domain"]

        for values_file in self.spec["helm_chart_values_files"]:
            if "secret" not in os.path.basename(
                values_file
            ) and not values_file.endswith(".jsonnet"):
                values_file = self.cluster.config_dir / values_file
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

        with (
            get_decrypted_files(
                self.cluster.config_dir / p
                for p in self.spec["helm_chart_values_files"]
            ) as values_files,
            ExitStack() as jsonnet_stack,
        ):

            chart_dir = HELM_CHARTS_DIR / self.spec["helm_chart"]
            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                f"--namespace={self.spec['name']}",
                self.spec["name"],
                chart_dir,
            ]

            # Add on rendered jsonnet values.yaml file for the chart
            rendered_values_path = jsonnet_stack.enter_context(
                render_jsonnet(
                    chart_dir / "values.jsonnet",
                    self.cluster.spec["name"],
                    self.spec["name"],
                )
            )

            cmd += ["--values", rendered_values_path]

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
