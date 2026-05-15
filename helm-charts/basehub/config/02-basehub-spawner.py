"""
Helpers for creating BinderSpawners

FIXME:
This file is defined in binderhub/binderspawner_mixin.py
and is copied to helm-chart/binderhub/values.yaml
by ci/check_embedded_chart_code.py

The BinderHub repo is just used as the distribution mechanism for this spawner,
BinderHub itself doesn't require this code.

Longer term options include:
- Move BinderSpawnerMixin to a separate Python package and include it in the Z2JH Hub
  image
- Override the Z2JH hub with a custom image built in this repository
- Duplicate the code here and in binderhub/binderspawner_mixin.py
"""

# Updates JupyterHub.spawner_class and KubeSpawner.modify_pod_hook to
# handle features introduced by the basehub chart, specifically those
# configured via:
#
# jupyterhub.custom.singleuserAdmin
#
import shlex

from kubernetes_asyncio.client.models import V1Container, V1VolumeMount
from kubespawner import KubeSpawner
from kubespawner.utils import get_k8s_model
from tornado import web
from traitlets import Bool, Unicode
from traitlets.config import Configurable
from z2jh import get_config

# This is copy-pasted exactly from https://github.com/jupyterhub/binderhub/blob/c6c5dc8fe73f81ca538c47b420b33f317c3aa8ae/helm-chart/binderhub/values.yaml#L87
# Should be updated every time the upstream code changes


class BinderSpawnerMixin(Configurable):
    """
    Mixin to convert a JupyterHub container spawner to a BinderHub spawner

    Container spawner must support the following properties that will be set
    via spawn options:
    - image: Container image to launch
    - token: JupyterHub API token
    """

    def __init__(self, *args, **kwargs):
        # Is this right? Is it possible to having multiple inheritance with both
        # classes using traitlets?
        # https://stackoverflow.com/questions/9575409/calling-parent-class-init-with-multiple-inheritance-whats-the-right-way
        # https://github.com/ipython/traitlets/pull/175
        super().__init__(*args, **kwargs)

    auth_enabled = Bool(
        False,
        help="""
        Enable authenticated binderhub setup.

        Requires `jupyterhub-singleuser` to be available inside the repositories
        being built.
        """,
        config=True,
    )

    cors_allow_origin = Unicode(
        "",
        help="""
        Origins that can access the spawned notebooks.

        Sets the Access-Control-Allow-Origin header in the spawned
        notebooks. Set to '*' to allow any origin to access spawned
        notebook servers.

        See also BinderHub.cors_allow_origin in binderhub config
        for controlling CORS policy for the BinderHub API endpoint.
        """,
        config=True,
    )

    def get_args(self):
        if self.auth_enabled:
            args = super().get_args()
        else:
            args = [
                "--ip=0.0.0.0",
                f"--port={self.port}",
                f"--NotebookApp.base_url={self.server.base_url}",
                f"--NotebookApp.token={self.user_options['token']}",
                "--NotebookApp.trust_xheaders=True",
            ]
            if self.default_url:
                args.append(f"--NotebookApp.default_url={self.default_url}")

            if self.cors_allow_origin:
                args.append("--NotebookApp.allow_origin=" + self.cors_allow_origin)
            # allow_origin=* doesn't properly allow cross-origin requests to single files
            # see https://github.com/jupyter/notebook/pull/5898
            if self.cors_allow_origin == "*":
                args.append("--NotebookApp.allow_origin_pat=.*")
            args += self.args
            # ServerApp compatibility: duplicate NotebookApp args
            for arg in list(args):
                if arg.startswith("--NotebookApp."):
                    args.append(arg.replace("--NotebookApp.", "--ServerApp."))
        return args

    def start(self):
        if not self.auth_enabled:
            if "token" not in self.user_options:
                raise web.HTTPError(400, "token required")
            if "image" not in self.user_options:
                raise web.HTTPError(400, "image required")
        if "image" in self.user_options:
            self.image = self.user_options["image"]
        return super().start()

    def get_env(self):
        env = super().get_env()
        if "repo_url" in self.user_options:
            env["BINDER_REPO_URL"] = self.user_options["repo_url"]
        for key in (
            "binder_ref_url",
            "binder_launch_host",
            "binder_persistent_request",
            "binder_request",
        ):
            if key in self.user_options:
                env[key.upper()] = self.user_options[key]
        return env


spawner_base_classes = [KubeSpawner]
if get_config("custom.binderhubUI.enabled"):
    spawner_base_classes = [BinderSpawnerMixin, KubeSpawner]

    # Set start timeout to 15minutes
    # This isn't ideal - they should start sooner than that! But
    # we recognize that sometimes pulling in a lot of images takes
    # a while, especially with node spinup. So we increase the timeout
    # to reduce our rate of false positives
    c.Spawner.start_timeout = 15 * 60


class BaseHubSpawner(*spawner_base_classes):
    def start(self, *args, **kwargs):
        """
        Modify admin users' spawners' non-list config based on
        `jupyterhub.custom.singleuserAdmin`.

        The list config is handled separately in by the
        `modify_pod_hook`.
        """
        custom_admin = get_config("custom.singleuserAdmin", {})
        if not (self.user.admin and custom_admin):
            return super().start(*args, **kwargs)

        admin_environment = custom_admin.get("extraEnv", {})
        self.environment.update(admin_environment)

        admin_service_account = custom_admin.get("serviceAccountName")
        if admin_service_account:
            self.service_account = admin_service_account

        return super().start(*args, **kwargs)


c.JupyterHub.spawner_class = BaseHubSpawner


def modify_pod_hook(spawner, pod):
    """
    Modify admin user's pod manifests based on *dict* config under
    `jupyterhub.custom.singleuserAdmin`.

    This hook is required to ensures that list config under
    `jupyterhub.custom.singleuserAdmin` are appended and not just
    overridden when a profile_list entry has a kubespawner_override
    modifying the same config.
    """
    # This if-statement is a patch to ensure that if there are no
    # initContainers, we can at least work with an empty list, so that
    # later appending actions do not fail.
    if pod.spec.init_containers is None:
        pod.spec.init_containers = []

    custom_admin = get_config("custom.singleuserAdmin", {})
    if spawner.user.admin and custom_admin:
        # Setup admin mounts only for admins
        for c in pod.spec.containers:
            if c.name == "notebook":
                notebook_container = c
                break
        else:
            raise Exception("No container named 'notebook' found in pod definition")

        admin_volume_mounts = custom_admin.get("extraVolumeMounts", {})
        # custom.singleuserAdmin.extraVolumeMounts is a dict now
        admin_volume_mounts = list(admin_volume_mounts.values())
        notebook_container.volume_mounts += [
            get_k8s_model(V1VolumeMount, obj) for obj in (admin_volume_mounts)
        ]

    # Setup iptables blocking for everyone
    block_ports = [2049, 20048, 111]
    commands = []
    for protocol in ("tcp", "udp"):
        for port in block_ports:
            commands.append(
                [
                    "iptables",
                    "--append",
                    "OUTPUT",
                    "--protocol",
                    protocol,
                    "--destination-port",
                    str(port),
                    "--jump",
                    "DROP",
                ]
            )

    shell_command = " && ".join([shlex.join(c) for c in commands])

    iptables_container = {
        "name": "block-nfs-access",
        "image": "quay.io/jupyterhub/k8s-network-tools:4.1.0",
        "securityContext": {
            "runAsUser": 0,
            "privileged": True,
            "capabilities": {"add": ["NET_ADMIN"]},
        },
        "command": ["/bin/sh", "-c", shell_command],
    }

    pod.spec.init_containers.append(get_k8s_model(V1Container, iptables_container))

    return pod


c.KubeSpawner.modify_pod_hook = modify_pod_hook
