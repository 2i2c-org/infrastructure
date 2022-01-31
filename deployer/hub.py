from auth import KeyProvider
import hashlib
import hmac
import json
import os
import sys
import subprocess
import tempfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from textwrap import dedent
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from utils import decrypt_file, print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


class Cluster:
    """
    A single k8s cluster we can deploy to
    """

    def __init__(self, spec):
        self.spec = spec
        self.hubs = [Hub(self, hub_yaml) for hub_yaml in self.spec["hubs"]]
        self.support = self.spec.get("support", {})

    @contextmanager
    def auth(self):
        if self.spec["provider"] == "gcp":
            yield from self.auth_gcp()
        elif self.spec["provider"] == "aws":
            yield from self.auth_aws()
        elif self.spec["provider"] == "azure":
            yield from self.auth_azure()
        elif self.spec["provider"] == "kubeconfig":
            yield from self.auth_kubeconfig()
        else:
            raise ValueError(f'Provider {self.spec["provider"]} not supported')

    def ensure_docker_credhelpers(self):
        """
        Setup credHelper for current hub's image registry.

        Most image registries (like ECR, GCP Artifact registry, etc) use
        a docker credHelper (https://docs.docker.com/engine/reference/commandline/login/#credential-helpers)
        to authenticate, rather than a username & password. This requires an
        entry per registry in ~/.docker/config.json.

        This method ensures the appropriate credential helper is present
        """
        image_name = self.spec["image_repo"]
        registry = image_name.split("/")[0]

        helper = None
        # pkg.dev is used by Google Cloud Artifact registry
        if registry.endswith("pkg.dev"):
            helper = "gcloud"

        if helper is not None:
            dockercfg_path = os.path.expanduser("~/.docker/config.json")
            try:
                with open(dockercfg_path) as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {}

            helpers = config.get("credHelpers", {})
            if helpers.get(registry) != helper:
                helpers[registry] = helper
                config["credHelpers"] = helpers
                with open(dockercfg_path, "w") as f:
                    json.dump(config, f, indent=4)

    def deploy_support(self):
        cert_manager_url = "https://charts.jetstack.io"
        cert_manager_version = "v1.3.1"

        print_colour("Adding cert-manager chart repo...")
        subprocess.check_call(
            [
                "helm",
                "repo",
                "add",
                "jetstack",
                cert_manager_url,
            ]
        )

        print_colour("Updating cert-manager chart repo...")
        subprocess.check_call(
            [
                "helm",
                "repo",
                "update",
            ]
        )

        print_colour("Provisioning cert-manager...")
        subprocess.check_call(
            [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                "--namespace=cert-manager",
                "cert-manager",
                "jetstack/cert-manager",
                f"--version={cert_manager_version}",
                "--set=installCRDs=true",
            ]
        )
        print_colour("Done!")

        print_colour("Provisioning support charts...")
        subprocess.check_call(["helm", "dep", "up", "support"])

        support_dir = (Path(__file__).parent.parent).joinpath("support")
        support_secrets_file = support_dir.joinpath("secrets.yaml")

        with tempfile.NamedTemporaryFile(mode="w") as f, decrypt_file(
            support_secrets_file
        ) as secret_file:
            yaml.dump(self.support.get("config", {}), f)
            f.flush()
            subprocess.check_call(
                [
                    "helm",
                    "upgrade",
                    "--install",
                    "--create-namespace",
                    "--namespace=support",
                    "support",
                    str(support_dir),
                    f"--values={secret_file}",
                    f"--values={f.name}",
                    "--wait",
                ]
            )
        print_colour("Done!")

    def auth_kubeconfig(self):
        """
        Context manager for authenticating with just a kubeconfig file

        For the duration of the contextmanager, we:
        1. Decrypt the file specified in kubeconfig.file with sops
        2. Set `KUBECONFIG` env var to our decrypted file path, so applications
           we call (primarily helm) will use that as config
        """
        config = self.spec["kubeconfig"]
        config_path = config["file"]

        with decrypt_file(config_path) as decrypted_key_path:
            # FIXME: Unset this after our yield
            os.environ["KUBECONFIG"] = decrypted_key_path
            yield

    def auth_aws(self):
        """
        Reads `aws` nested config and temporarily sets environment variables
        like `KUBECONFIG`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY`
        before trying to authenticate with the `aws eks update-kubeconfig` or
        the `kops export kubecfg --admin` commands.

        Finally get those environment variables to the original values to prevent
        side-effects on existing local configuration.
        """
        config = self.spec["aws"]
        key_path = config["key"]
        cluster_type = config["clusterType"]
        cluster_name = config["clusterName"]
        region = config["region"]

        if cluster_type == "kops":
            state_store = config["stateStore"]

        with tempfile.NamedTemporaryFile() as kubeconfig:
            orig_kubeconfig = os.environ.get("KUBECONFIG", None)
            orig_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
            orig_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
            try:
                with decrypt_file(key_path) as decrypted_key_path:

                    decrypted_key_abspath = os.path.abspath(decrypted_key_path)
                    if not os.path.isfile(decrypted_key_abspath):
                        raise FileNotFoundError("The decrypted key file does not exist")
                    with open(decrypted_key_abspath) as f:
                        creds = json.load(f)

                    os.environ["AWS_ACCESS_KEY_ID"] = creds["AccessKey"]["AccessKeyId"]
                    os.environ["AWS_SECRET_ACCESS_KEY"] = creds["AccessKey"][
                        "SecretAccessKey"
                    ]

                os.environ["KUBECONFIG"] = kubeconfig.name

                if cluster_type == "kops":
                    subprocess.check_call(
                        [
                            "kops",
                            "export",
                            "kubecfg",
                            "--admin",
                            f"--name={cluster_name}",
                            f"--state={state_store}",
                        ]
                    )
                else:
                    subprocess.check_call(
                        [
                            "aws",
                            "eks",
                            "update-kubeconfig",
                            f"--name={cluster_name}",
                            f"--region={region}",
                        ]
                    )

                yield
            finally:
                if orig_kubeconfig is not None:
                    os.environ["KUBECONFIG"] = orig_kubeconfig
                if orig_access_key_id is not None:
                    os.environ["AWS_ACCESS_KEY_ID"] = orig_access_key_id
                if orig_kubeconfig is not None:
                    os.environ["AWS_SECRET_ACCESS_KEY"] = orig_secret_access_key

    def auth_azure(self):
        """
        Read `azure` nested config, login to Azure with a Service Principal,
        activate the appropriate subscription, then authenticate against the
        cluster using `az aks get-credentials`.
        """
        config = self.spect["azure"]
        key_path = config["key"]
        cluster = config["cluster"]
        resource_group = config["resource_group"]

        with tempfile.NamedTemporaryFile() as kubeconfig:
            orig_kubeconfig = os.environ.get("KUBECONFIG", None)

            try:
                os.environ["KUBECONFIG"] = kubeconfig.name

                with decrypt_file(key_path) as decrypted_key_path:

                    decrypted_key_abspath = os.path.abspath(decrypted_key_path)
                    if not os.path.isfile(decrypted_key_abspath):
                        raise FileNotFoundError("The decrypted key file does not exist")

                    with open(decrypted_key_path) as f:
                        service_principal = json.load(f)

                # Login to Azure
                subprocess.check_call(
                    [
                        "az",
                        "login",
                        "--service-principal",
                        f"--username={service_principal['service_principal_id']}",
                        f"--password={service_principal['service_principal_password']}",
                        f"--tenant={service_principal['tenant_id']}",
                    ]
                )

                # Set the Azure subscription
                subprocess.check_call(
                    [
                        "az",
                        "account",
                        "set",
                        f"--subscription={service_principal['subscription_id']}",
                    ]
                )

                # Get cluster creds
                subprocess.check_call(
                    [
                        "az",
                        "aks",
                        "get-credentials",
                        f"--name={cluster}",
                        f"--resource-group={resource_group}",
                    ]
                )

                yield
            finally:
                if orig_kubeconfig is not None:
                    os.environ["KUBECONFIG"] = orig_kubeconfig

    def auth_gcp(self):
        config = self.spec["gcp"]
        key_path = config["key"]
        project = config["project"]
        # If cluster is regional, it'll have a `region` key set.
        # Else, it'll just have a `zone` key set. Let's respect either.
        location = config.get("zone", config.get("region"))
        cluster = config["cluster"]
        with tempfile.NamedTemporaryFile() as kubeconfig:
            orig_kubeconfig = os.environ.get("KUBECONFIG")
            try:
                os.environ["KUBECONFIG"] = kubeconfig.name
                with decrypt_file(key_path) as decrypted_key_path:
                    subprocess.check_call(
                        [
                            "gcloud",
                            "auth",
                            "activate-service-account",
                            f"--key-file={os.path.abspath(decrypted_key_path)}",
                        ]
                    )

                subprocess.check_call(
                    [
                        "gcloud",
                        "container",
                        "clusters",
                        # --zone works with regions too
                        f"--zone={location}",
                        f"--project={project}",
                        "get-credentials",
                        cluster,
                    ]
                )

                yield
            finally:
                if orig_kubeconfig is not None:
                    os.environ["KUBECONFIG"] = orig_kubeconfig


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
                                "https://github.com/2i2c-org/pilot-homepage",
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
                                    if [[ $(git ls-remote --heads origin {self.spec["name"]} | wc -c) -ne 0 ]]; then
                                        git reset --hard origin/{self.spec["name"]};
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

    def unset_env_var(self, env_var, old_env_var_value):
        """
        If the old environment variable's value exists, replace the current one with the old one
        If the old environment variable's value does not exist, delete the current one
        """

        if env_var in os.environ:
            del os.environ[env_var]
        if old_env_var_value is not None:
            os.environ[env_var] = old_env_var_value

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

        docs_token = hmac.new(
            secret_key, f'docs-{self.spec["name"]}'.encode(), hashlib.sha256
        ).hexdigest()
        if (
            "docs_service" in self.spec["config"].keys()
            and self.spec["config"]["docs_service"]["enabled"]
        ):
            generated_config["jupyterhub"]["hub"]["services"]["docs"] = {
                "url": f'http://docs-service.{self.spec["name"]}',
                "apiToken": docs_token,
            }

        # FIXME: Have a templates config somewhere? Maybe in Chart.yaml
        # FIXME: This is a hack. Fix it.
        if hub_helm_chart != "basehub":
            generated_config = {"basehub": generated_config}

        # LOLSOB FIXME
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
        # Ensure helm charts are up to date
        os.chdir("helm-charts")
        subprocess.check_call(["helm", "dep", "up", "basehub"])
        if self.spec["helm_chart"] == "daskhub":
            subprocess.check_call(["helm", "dep", "up", "daskhub"])
        os.chdir("..")

        # Check if this cluster has any secret config. If yes, read it in.
        secret_config_path = (
            Path(os.getcwd()).joinpath(
            "secrets", "config", "hubs",
            f'{self.cluster.spec["name"]}.cluster.yaml')
        )

        secret_hub_config = {}
        if os.path.exists(secret_config_path):
            with decrypt_file(secret_config_path) as decrypted_file_path:
                with open(decrypted_file_path) as f:
                    secret_config = yaml.load(f)

            if secret_config.get("hubs", {}):
                hubs = secret_config["hubs"]
                current_hub = next(
                    (hub for hub in hubs if hub["name"] == self.spec["name"]), {}
                )
                # Support domain name overrides
                if "domain" in current_hub:
                    self.spec["domain"] = current_hub["domain"]
                secret_hub_config = current_hub.get("config", {})

        generated_values = self.get_generated_config(auth_provider, secret_key)

        with tempfile.NamedTemporaryFile(
            mode="w"
        ) as values_file, tempfile.NamedTemporaryFile(
            mode="w"
        ) as generated_values_file, tempfile.NamedTemporaryFile(
            mode="w"
        ) as secret_values_file:
            json.dump(self.spec["config"], values_file)
            json.dump(generated_values, generated_values_file)
            json.dump(secret_hub_config, secret_values_file)
            values_file.flush()
            generated_values_file.flush()
            secret_values_file.flush()

            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                "--wait",
                f"--namespace={self.spec['name']}",
                self.spec["name"],
                os.path.join("helm-charts", self.spec["helm_chart"]),
                # Ordering matters here - config explicitly mentioned in clu should take
                # priority over our generated values. Based on how helm does overrides, this means
                # we should put the config from config/hubs last.
                f"--values={generated_values_file.name}",
                f"--values={values_file.name}",
                f"--values={secret_values_file.name}",
            ]

            print_colour(f"Running {' '.join(cmd)}")
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
