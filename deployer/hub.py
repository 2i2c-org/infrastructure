import hashlib
import hmac
import json
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

from auth import KeyProvider
from file_acquisition import get_decrypted_file, get_decrypted_files
from ruamel.yaml import YAML
from utils import print_colour

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

    def get_generated_config(self, auth_provider: KeyProvider, secret_key):
        """
        Generate config automatically for each hub

        WARNING: MIGHT CONTAINS SECRET VALUES!
        """
        if self.spec["helm_chart"] == "binderhub":
            # For Google Artifact registry, this takes the following form:
            # {LOCATION}-docker.pkg.dev
            # If the zone of the cluster is us-central1-b, then the location is us-central1
            registry_url = f"{'-'.join(self.cluster.spec['gcp']['zone'].split('-')[:2])}-docker.pkg.dev"

            # NOTE: We are hard-coding config for using Google Artifact Registry here.
            # We should not. Instead we should provide a way to support as many container
            # registries as BinderHub supports. We are hard-coding this config here
            # because we need to generate parts of it from the cluster object spec,
            # so to generalise, we may have to live with some copy-pasting of certain
            # values such as cluster project and location.
            generated_config = {
                "binderhub": {
                    "registry": {"url": f"https://{registry_url}"},
                    "config": {
                        "BinderHub": {
                            "hub_url": f"https://hub.{self.spec['domain']}",
                            # For Google Artifact registry, this takes the following form:
                            # {registry_url}/{PROJECT_ID}/{REPOSITORY}-registry/{IMAGE}-
                            # REPOSITORY and IMAGE will both be the hub namespace
                            "image_prefix": f"{registry_url}/{self.cluster.spec['gcp']['project']}/{self.spec['name']}-registry/{self.spec['name']}-",
                        },
                        "DockerRegistry": {
                            "token_url": f"https://{registry_url}/v2/token?service="
                        },
                    },
                    "ingress": {
                        "hosts": [self.spec["domain"]],
                        "tls": [
                            {
                                "secretName": "https-auto-tls-binder",
                                "hosts": [self.spec["domain"]],
                            }
                        ],
                    },
                    "jupyterhub": {
                        "ingress": {
                            "hosts": [f"hub.{self.spec['domain']}"],
                            "tls": [
                                {
                                    "secretName": "https-auto-tls-hub",
                                    "hosts": [f"hub.{self.spec['domain']}"],
                                }
                            ],
                        }
                    },
                }
            }
        else:
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
                    "singleuser": {
                        # If image_repo isn't set, just have an empty image dict
                        "image": {"name": self.cluster.spec["image_repo"]}
                        if "image_repo" in self.cluster.spec
                        else {},
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
                                "securityContext": {
                                  "runAsUser": 0
                                },
                                "volumeMounts": [
                                    {
                                        "name": "custom-templates",
                                        "mountPath": "/srv/repo",
                                    }
                                ],
                            }
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
        #
        # Allow explicilty ignoring auth0 setup
        if self.spec["auth0"].get("enabled", True):
            # Auth0 sends users back to this URL after they authenticate
            callback_url = f"https://{self.spec['domain']}/hub/oauth_callback"
            # Users are redirected to this URL after they log out
            logout_url = f"https://{self.spec['domain']}"
            client = auth_provider.ensure_client(
                name=self.spec["auth0"].get(
                    "application_name",
                    f"{self.cluster.spec['name']}-{self.spec['name']}",
                ),
                callback_url=callback_url,
                logout_url=logout_url,
                connection_name=self.spec["auth0"]["connection"],
                connection_config=self.spec["auth0"].get(
                    self.spec["auth0"]["connection"], {}
                ),
            )
            # NOTE: Some dictionary merging might make these lines prettier/more readable.
            # Since Auth0 is enabled, we set the authenticator_class to the Auth0OAuthenticator class
            generated_config["jupyterhub"]["hub"]["config"]["JupyterHub"] = {
                "authenticator_class": "oauthenticator.auth0.Auth0OAuthenticator"
            }
            generated_config["jupyterhub"]["hub"]["config"][
                "Auth0OAuthenticator"
            ] = auth_provider.get_client_creds(client, self.spec["auth0"]["connection"])

        return self.apply_hub_helm_chart_fixes(generated_config, secret_key)

    def apply_hub_helm_chart_fixes(self, generated_config, secret_key):
        """
        Modify generated_config based on what hub helm chart we're using.

        Different hub helm charts require different pre-set config. For example,
        anything deriving from 'basehub' needs all config to be under a 'basehub'
        config. dask hubs require apiTokens, etc.

        Ideally, these would be done declaratively. Until then, let's put all of
        them in this function.
        """
        # FIXME: This section can be removed upon resolution of the below linked issue, where we would
        #        instead just define a JupyterHub service under hub.services and
        #        rely on the JupyterHub Helm chart to generate an api token if
        #        needed.
        #
        #        Blocked by https://github.com/dask/dask-gateway/issues/473 and a
        #        release including it.
        #
        if self.spec["helm_chart"] == "daskhub":
            generated_config = {"basehub": generated_config}

            gateway_token = hmac.new(
                secret_key, b"gateway-" + self.spec["name"].encode(), hashlib.sha256
            ).hexdigest()
            generated_config["dask-gateway"] = {
                "gateway": {"auth": {"jupyterhub": {"apiToken": gateway_token}}}
            }
            generated_config["basehub"].setdefault("jupyterhub", {}).setdefault(
                "hub", {}
            ).setdefault("services", {})["dask-gateway"] = {"apiToken": gateway_token}

        elif self.spec["helm_chart"] == "binderhub":
            gateway_token = hmac.new(
                secret_key, b"gateway-" + self.spec["name"].encode(), hashlib.sha256
            ).hexdigest()
            generated_config["dask-gateway"] = {
                "gateway": {"auth": {"jupyterhub": {"apiToken": gateway_token}}}
            }
            generated_config["binderhub"].setdefault("jupyterhub", {}).setdefault(
                "hub", {}
            ).setdefault("services", {})["dask-gateway"] = {"apiToken": gateway_token}

        return generated_config

    def exec_homes_shell(self):
        """
        Pop a shell with the home directories of the given hub mounted

        Homes will be mounter under /home
        """
        # Name pod to include hub name so we don't end up in wrong one
        pod_name = f'{self.spec["name"]}-shell'
        pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "spec": {
                "terminationGracePeriodSeconds": 1,
                "automountServiceAccountToken": False,
                "volumes": [
                    # This PVC is created by basehub
                    {"name": "home", "persistentVolumeClaim": {"claimName": "home-nfs"}}
                ],
                "containers": [
                    {
                        "name": pod_name,
                        # Use ubuntu image so we get better gnu rm
                        "image": "ubuntu:jammy",
                        "stdin": True,
                        "stdinOnce": True,
                        "tty": True,
                        "volumeMounts": [
                            {
                                "name": "home",
                                "mountPath": "/home",
                            }
                        ],
                    }
                ],
            },
        }

        cmd = [
            "kubectl",
            "-n",
            self.spec["name"],
            "run",
            "--rm",  # Remove pod when we're done
            "-it",  # Give us a shell!
            "--overrides",
            json.dumps(pod),
            "--image",
            # Use ubuntu image so we get GNU rm and other tools
            # Should match what we have in our pod definition
            "ubuntu:jammy",
            pod_name,
            "--",
            "/bin/bash",
            "-l",
        ]

        subprocess.check_call(cmd)

    def deploy(self, auth_provider, secret_key, dask_gateway_version):
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

        generated_values = self.get_generated_config(auth_provider, secret_key)

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

            # Add on the values files
            for values_file in values_files:
                cmd.append(f"--values={values_file}")

            # join method will fail on the PosixPath element if not transformed
            # into a string first
            print_colour(f"Running {' '.join([str(c) for c in cmd])}")
            subprocess.check_call(cmd)
