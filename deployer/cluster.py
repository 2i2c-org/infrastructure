import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .file_acquisition import get_decrypted_file, get_decrypted_files
from .hub import Hub
from .utils import print_colour, unset_env_vars


class Cluster:
    """
    A single k8s cluster we can deploy to
    """

    def __init__(self, spec, config_path):
        self.spec = spec
        self.config_path = config_path
        self.hubs = [Hub(self, hub_spec) for hub_spec in self.spec["hubs"]]
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

    def deploy_support(self, cert_manager_version):
        cert_manager_url = "https://charts.jetstack.io"

        print_colour("Provisioning cert-manager...")
        subprocess.check_call(
            [
                "kubectl",
                "apply",
                "-f",
                f"https://github.com/cert-manager/cert-manager/releases/download/{cert_manager_version}/cert-manager.crds.yaml",
            ]
        )
        subprocess.check_call(
            [
                "helm",
                "upgrade",
                "cert-manager",  # given release name (aka. installation name)
                "cert-manager",  # helm chart to install
                f"--repo={cert_manager_url}",
                "--install",
                "--create-namespace",
                "--namespace=cert-manager",
                f"--version={cert_manager_version}",
            ]
        )
        print_colour("Done!")

        print_colour("Provisioning support charts...")

        support_dir = (Path(__file__).parent.parent).joinpath("helm-charts", "support")
        subprocess.check_call(["helm", "dep", "up", support_dir])

        # contains both encrypted and unencrypted values files
        values_file_paths = [support_dir.joinpath("enc-support.secret.values.yaml")] + [
            self.config_path.joinpath(p)
            for p in self.support["helm_chart_values_files"]
        ]

        with get_decrypted_files(values_file_paths) as values_files:
            cmd = [
                "helm",
                "upgrade",
                "--install",
                "--create-namespace",
                "--namespace=support",
                "--wait",
                "support",
                str(support_dir),
            ]

            for values_file in values_files:
                cmd.append(f"--values={values_file}")

            print_colour(f"Running {' '.join([str(c) for c in cmd])}")
            subprocess.check_call(cmd)

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
        config_path = self.config_path.joinpath(config["file"])

        with get_decrypted_file(config_path) as decrypted_key_path, unset_env_vars(
            ["KUBECONFIG"]
        ):
            os.environ["KUBECONFIG"] = decrypted_key_path
            yield

    def auth_aws(self):
        """
        Reads `aws` nested config and temporarily sets environment variables
        like `KUBECONFIG`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY`
        before trying to authenticate with the `aws eks update-kubeconfig` command.

        Finally get those environment variables to the original values to prevent
        side-effects on existing local configuration.
        """
        config = self.spec["aws"]
        key_path = self.config_path.joinpath(config["key"])
        cluster_name = config["clusterName"]
        region = config["region"]

        # Unset all env vars that start with AWS_, as that might affect the aws
        # commandline we call. This could make some weird error messages.
        unset_envs = ["KUBECONFIG"] + [k for k in os.environ if k.startswith("AWS_")]

        with tempfile.NamedTemporaryFile() as kubeconfig, unset_env_vars(unset_envs):
            with get_decrypted_file(key_path) as decrypted_key_path:
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

    def auth_azure(self):
        """
        Read `azure` nested config, login to Azure with a Service Principal,
        activate the appropriate subscription, then authenticate against the
        cluster using `az aks get-credentials`.
        """
        config = self.spect["azure"]
        key_path = self.config_path.joinpath(config["key"])
        cluster = config["cluster"]
        resource_group = config["resource_group"]

        with tempfile.NamedTemporaryFile() as kubeconfig, unset_env_vars(
            ["KUBECONFIG"]
        ):
            os.environ["KUBECONFIG"] = kubeconfig.name

            with get_decrypted_file(key_path) as decrypted_key_path:
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

    def auth_gcp(self):
        config = self.spec["gcp"]
        key_path = self.config_path.joinpath(config["key"])
        project = config["project"]
        # If cluster is regional, it'll have a `region` key set.
        # Else, it'll just have a `zone` key set. Let's respect either.
        location = config.get("zone", config.get("region"))
        cluster = config["cluster"]
        with tempfile.NamedTemporaryFile() as kubeconfig:
            # CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE is removed as the action of
            # "gcloud auth activate-server-account" will be secondary to it
            # otherwise, and this env var can be set by GitHub Actions we use
            # before using this deployer script to deploy hubs to clusters.
            orig_cloudsdk_auth_credential_file_override = os.environ.pop(
                "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE", None
            )
            orig_kubeconfig = os.environ.get("KUBECONFIG")
            try:
                os.environ["KUBECONFIG"] = kubeconfig.name
                with get_decrypted_file(key_path) as decrypted_key_path:
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
                if orig_cloudsdk_auth_credential_file_override is not None:
                    os.environ[
                        "CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE"
                    ] = orig_cloudsdk_auth_credential_file_override
