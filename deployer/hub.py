import json
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

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

    def get_generated_config(self):
        """
        Generate config automatically for each hub
        """
        generated_config = {
            "jupyterhub": {
                "proxy": {"https": {"hosts": [self.spec["domain"]]}},
                "ingress": {
                    "hosts": [self.spec["domain"]],
                    "tls": [
                        {
                            "secretName": "https-auto-tls",
                            "hosts": [self.spec["domain"]],
                        }
                    ],
                },
                "hub": {
                    "config": {},
                    "initContainers": [
                        {
                            "name": "templates-clone",
                            "image": "alpine/git",
                            "args": [
                                "clone",
                                "--",
                                "https://github.com/2i2c-org/default-hub-homepage",
                                "/srv/repo",
                            ],
                            "securityContext": {
                                "runAsUser": 1000,
                                "runAsGroup": 1000,
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                            },
                            "volumeMounts": [
                                {
                                    "name": "custom-templates",
                                    "mountPath": "/srv/repo",
                                }
                            ],
                        },
                        {
                            "name": "templates-ownership-fix",
                            "image": "alpine/git",
                            "command": ["/bin/sh"],
                            "args": [
                                "-c",
                                "ls -lhd /srv/repo && chown 1000:1000 /srv/repo && ls -lhd /srv/repo",
                            ],
                            "securityContext": {"runAsUser": 0},
                            "volumeMounts": [
                                {
                                    "name": "custom-templates",
                                    "mountPath": "/srv/repo",
                                }
                            ],
                        },
                    ],
                    "extraContainers": [
                        {
                            "name": "templates-sync",
                            "image": "alpine/git",
                            "workingDir": "/srv/repo",
                            "command": ["/bin/sh"],
                            "args": [
                                "-c",
                                dedent(
                                    f"""\
                                    ls -lhd /srv/repo;
                                    while true; do git fetch origin;
                                    if [[ $(git ls-remote --heads origin {self.cluster.spec["name"]}-{self.spec["name"]} | wc -c) -ne 0 ]]; then
                                        git reset --hard origin/{self.cluster.spec["name"]}-{self.spec["name"]};
                                    else
                                        git reset --hard origin/master;
                                    fi
                                    sleep 5m; done
                                    """
                                ),
                            ],
                            "securityContext": {
                                "runAsUser": 1000,
                                "runAsGroup": 1000,
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                            },
                            "volumeMounts": [
                                {
                                    "name": "custom-templates",
                                    "mountPath": "/srv/repo",
                                }
                            ],
                        }
                    ],
                    "extraVolumes": [{"name": "custom-templates", "emptyDir": {}}],
                    "extraVolumeMounts": [
                        {
                            "mountPath": "/usr/local/share/jupyterhub/custom_templates",
                            "name": "custom-templates",
                            "subPath": "templates",
                        },
                        {
                            "mountPath": "/usr/local/share/jupyterhub/static/extra-assets",
                            "name": "custom-templates",
                            "subPath": "extra-assets",
                        },
                    ],
                },
            },
        }

        # Due to nesting of charts on top of the basehub, our generated basehub
        # config may need to be nested as well.
        if self.spec["helm_chart"] == "daskhub":
            generated_config = {"basehub": generated_config}
        elif self.spec["helm_chart"] == "binderhub":
            generated_config = {}

        return generated_config

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

        generated_values = self.get_generated_config()

        if self.spec["helm_chart"] == "daskhub":
            # Install CRDs for daskhub before deployment
            manifest_urls = [
                f"https://raw.githubusercontent.com/dask/dask-gateway/{dask_gateway_version}/resources/helm/dask-gateway/crds/daskclusters.yaml",
                f"https://raw.githubusercontent.com/dask/dask-gateway/{dask_gateway_version}/resources/helm/dask-gateway/crds/traefik.yaml",
            ]

            for manifest_url in manifest_urls:
                subprocess.check_call(["kubectl", "apply", "-f", manifest_url])

        with tempfile.NamedTemporaryFile(
            mode="w"
        ) as generated_values_file, get_decrypted_files(
            self.cluster.config_path.joinpath(p)
            for p in self.spec["helm_chart_values_files"]
        ) as values_files:
            json.dump(generated_values, generated_values_file)
            generated_values_file.flush()

            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                "--wait",
                f"--namespace={self.spec['name']}",
                self.spec["name"],
                helm_charts_dir.joinpath(self.spec["helm_chart"]),
                # Ordering matters here - config explicitly mentioned in cli should take
                # priority over our generated values. Based on how helm does overrides, this means
                # we should put the config from cluster.yaml last.
                f"--values={generated_values_file.name}",
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
