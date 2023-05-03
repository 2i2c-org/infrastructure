import subprocess
from pathlib import Path

from ruamel.yaml import YAML

from .file_acquisition import get_decrypted_file, get_decrypted_files
from .utils import print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)
helm_charts_dir = Path(__file__).parent.parent.joinpath("helm-charts")


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

        if self.spec["helm_chart"] == "daskhub":
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
        ) as values_files:
            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                "--wait",
                f"--namespace={self.spec['name']}",
                self.spec["name"],
                helm_charts_dir.joinpath(self.spec["helm_chart"]),
            ]

            if dry_run:
                cmd.append("--dry-run")

            if debug:
                cmd.append("--debug")

            # Add on the values files
            for values_file in values_files:
                cmd.append(f"--values={values_file}")

            # join method will fail on the PosixPath element if not transformed
            # into a string first
            print_colour(f"Running {' '.join([str(c) for c in cmd])}")
            subprocess.check_call(cmd)
