# Initially copied from https://github.com/dask/helm-chart/blob/main/daskhub/values.yaml
# 1. Sets `DASK_GATEWAY__PROXY_ADDRESS` in the singleuser environment.
# 2. Adds the URL for the Dask Gateway JupyterHub service.
import os

from z2jh import get_config

if get_config("custom.daskhubSetup.enabled"):
    # Default all users on hubs with dask-gateway to use JupyterLab
    c.Spawner.default_url = "/lab"

    # Add an extra label that allows user pods to talk to the proxy pod
    # in clusters with networkPolicy enabled so kernels can talk to the
    # dask-gateway service via the proxy
    c.KubeSpawner.extra_labels.update(
        {"hub.jupyter.org/network-access-proxy-http": "true"}
    )
    # These are set by jupyterhub.
    release_name = os.environ["HELM_RELEASE_NAME"]
    release_namespace = os.environ["POD_NAMESPACE"]
    if "PROXY_HTTP_SERVICE_HOST" in os.environ:
        # https is enabled, we want to use the internal http service.
        gateway_address = "http://{}:{}/services/dask-gateway/".format(
            os.environ["PROXY_HTTP_SERVICE_HOST"],
            os.environ["PROXY_HTTP_SERVICE_PORT"],
        )
        print(f"Setting DASK_GATEWAY__ADDRESS {gateway_address} from HTTP service")
    else:
        gateway_address = "http://proxy-public/services/dask-gateway"
        print(f"Setting DASK_GATEWAY__ADDRESS {gateway_address}")
    # Internal address to connect to the Dask Gateway.
    c.KubeSpawner.environment.setdefault("DASK_GATEWAY__ADDRESS", gateway_address)
    # Internal address for the Dask Gateway proxy.
    c.KubeSpawner.environment.setdefault(
        "DASK_GATEWAY__PROXY_ADDRESS",
        "gateway://traefik-{}-dask-gateway.{}:80".format(
            release_name, release_namespace
        ),
    )
    # Relative address for the dashboard link.
    c.KubeSpawner.environment.setdefault(
        "DASK_GATEWAY__PUBLIC_ADDRESS", "/services/dask-gateway/"
    )
    # Use JupyterHub to authenticate with Dask Gateway.
    c.KubeSpawner.environment.setdefault("DASK_GATEWAY__AUTH__TYPE", "jupyterhub")

    # Add some settings for dask gateway via environment variables
    # https://docs.dask.org/en/latest/configuration.html has more information
    # Kubernetes env variable expansion via `{{}}` is used here. See
    # https://kubernetes.io/docs/tasks/inject-data-application/define-interdependent-environment-variables/
    # for more information
    c.KubeSpawner.environment.update(
        {
            # Specify what image dask-gateway workers and schedulers should use
            "DASK_GATEWAY__CLUSTER__OPTIONS__IMAGE": "{{JUPYTER_IMAGE_SPEC}}",
            "DASK_GATEWAY__CLUSTER__OPTIONS__ENVIRONMENT": '{{"SCRATCH_BUCKET": "$(SCRATCH_BUCKET)", "PANGEO_SCRATCH": "$(PANGEO_SCRATCH)"}}',
            "DASK_DISTRIBUTED__DASHBOARD__LINK": "{{JUPYTERHUB_SERVICE_PREFIX}}proxy/{{port}}/status",
        }
    )

    # Adds Dask Gateway as a JupyterHub service to make the gateway available at
    # {HUB_URL}/services/dask-gateway
    service_url = "http://traefik-{}-dask-gateway.{}".format(
        release_name, release_namespace
    )
    for service in c.JupyterHub.services:
        if service["name"] == "dask-gateway":
            if not service.get("url", None):
                print("Adding dask-gateway service URL")
                service.setdefault("url", service_url)
            break
    else:
        print("dask-gateway service not found, this should not happen!")
