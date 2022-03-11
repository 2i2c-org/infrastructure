import hashlib
import hmac
import json
import os
import subprocess
import sys
import tempfile
import pytest

from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from textwrap import dedent
from ruamel.yaml import YAML

from auth_client_provider import ClientProvider
from utils import print_colour
from file_acquisition import get_decrypted_file, get_decrypted_files

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

    def get_generated_config(self, auth_provider: ClientProvider, secret_key):
        """
        Generate config automatically for each hub

        WARNING: MIGHT CONTAINS SECRET VALUES!
        """

        generated_config = {
            "jupyterhub": {
                "proxy": {"https": {"hosts": [self.spec["domain"]]}},
                "ingress": {
                    "hosts": [self.spec["domain"]],
                    "tls": [
                        {"secretName": "https-auto-tls", "hosts": [self.spec["domain"]]}
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
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                            },
                            "volumeMounts": [
                                {"name": "custom-templates", "mountPath": "/srv/repo"}
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
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                            },
                            "volumeMounts": [
                                {"name": "custom-templates", "mountPath": "/srv/repo"}
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

        # Allow explicilty ignoring auth0/cilogon setup
        if self.spec["auth0"].get("enabled", False) and self.spec["cilogon"].get(
            "enabled", False
        ):
            return self.apply_hub_helm_chart_fixes(generated_config, secret_key)

        # Send users back to this URL after they authenticate
        callback_url = f"https://{self.spec['domain']}/hub/oauth_callback"
        # Users are redirected to this URL after they log out
        logout_url = f"https://{self.spec['domain']}"
        # Human readable name of the client OAuth2 application
        client_name = f"{self.cluster.spec['name']}-{self.spec['name']}"
        connection_config = None

        if self.spec["auth0"].get("enabled", True):
            connection_name = self.spec["auth0"]["connection"]
            connection_config = self.spec["auth0"].get(
                self.spec["auth0"]["connection"], {}
            )
            authenticator_class_entrypoint = "auth0"
            authenticator_class_name = "Auth0OAuthenticator"
        elif self.spec["cilogon"].get("enabled", True):
            connection_name = self.spec["cilogon"]["allowed_idps"]
            connection_config = self.cluster.config_path.joinpath(
                "enc-cilogon-clients.secret.yaml"
            )
            authenticator_class_entrypoint = "cilogon"
            authenticator_class_name = "CILogonOAuthenticator"

        client = auth_provider.ensure_client(
            name=client_name,
            callback_url=callback_url,
            logout_url=logout_url,
            connection_name=connection_name,
            connection_config=connection_config,
        )

        # NOTE: Some dictionary merging might make these lines prettier/more readable.
        generated_config["jupyterhub"]["hub"]["config"]["JupyterHub"] = {
            "authenticator_class": authenticator_class_entrypoint
        }
        generated_config["jupyterhub"]["hub"]["config"][
            authenticator_class_name
        ] = auth_provider.get_client_creds(client, connection_name, callback_url)

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
        hub_helm_chart = self.spec["helm_chart"]

        # Generate a token for the hub health service
        hub_health_token = hmac.new(
            secret_key, b"health-" + self.spec["name"].encode(), hashlib.sha256
        ).hexdigest()
        # Describe the hub health service
        generated_config.setdefault("jupyterhub", {}).setdefault("hub", {}).setdefault(
            "services", {}
        )["hub-health"] = {"apiToken": hub_health_token, "admin": True}

        # FIXME: Have a templates config somewhere? Maybe in Chart.yaml
        # FIXME: This is a hack. Fix it.
        if hub_helm_chart != "basehub":
            generated_config = {"basehub": generated_config}

        # FIXME: This section can be fixed upon resolution of:
        # https://github.com/dask/dask-gateway/issues/473
        if hub_helm_chart == "daskhub":
            gateway_token = hmac.new(
                secret_key, b"gateway-" + self.spec["name"].encode(), hashlib.sha256
            ).hexdigest()
            generated_config["dask-gateway"] = {
                "gateway": {"auth": {"jupyterhub": {"apiToken": gateway_token}}}
            }
            generated_config["basehub"]["jupyterhub"]["hub"]["services"][
                "dask-gateway"
            ] = {"apiToken": gateway_token}

        return generated_config

    def deploy(self, auth_provider, secret_key, skip_hub_health_test=False):
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
            # Can't test without deploying, since our service token isn't set by default
            subprocess.check_call(cmd)

            if not skip_hub_health_test:

                # FIXMEL: Clean this up
                if self.spec["helm_chart"] != "basehub":
                    service_api_token = generated_values["basehub"]["jupyterhub"][
                        "hub"
                    ]["services"]["hub-health"]["apiToken"]
                else:
                    service_api_token = generated_values["jupyterhub"]["hub"][
                        "services"
                    ]["hub-health"]["apiToken"]

                hub_url = f'https://{self.spec["domain"]}'

                # On failure, pytest prints out params to the test that failed.
                # This can contain sensitive info - so we hide stderr
                # FIXME: Don't use pytest - just call a function instead
                print_colour("Running hub health check...")
                # Show errors locally but redirect on CI
                gh_ci = os.environ.get("CI", "false")
                pytest_args = [
                    "-q",
                    "deployer/tests",
                    "--hub-url",
                    hub_url,
                    "--api-token",
                    service_api_token,
                    "--hub-type",
                    self.spec["helm_chart"],
                ]
                if gh_ci == "true":
                    print_colour("Testing on CI, not printing output")
                    with open(os.devnull, "w") as dn, redirect_stderr(
                        dn
                    ), redirect_stdout(dn):
                        exit_code = pytest.main(pytest_args)
                else:
                    print_colour("Testing locally, do not redirect output")
                    exit_code = pytest.main(pytest_args)
                if exit_code != 0:
                    print("Health check failed!", file=sys.stderr)
                    sys.exit(exit_code)
                else:
                    print_colour("Health check succeeded!")
