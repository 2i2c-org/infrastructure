import os

from z2jh import get_config

usage_quotas_enabled = get_config("custom.usageQuotas.enabled")
if usage_quotas_enabled:
    from jupyterhub_usage_quotas import setup_usage_quotas

    setup_usage_quotas(c)

    c.JupyterHub.services["usage-quota"] = {
        "url": "http://hub:9000",
        "display": True,
        "oauth_no_confirm": True,
        "command": [
            "python",
            "-m",
            "jupyterhub_usage_quotas.services.usage_viewer",
            "--config-files=/usr/local/etc/jupyterhub/jupyterhub_config.d/jupyterhub_usage_quotas_config.py",
        ],
        "environment": {
            "JUPYTERHUB_USAGE_QUOTAS_PROMETHEUS_USERNAME": os.environ.get(
                "JUPYTERHUB_USAGE_QUOTAS_PROMETHEUS_USERNAME"
            ),
            "JUPYTERHUB_USAGE_QUOTAS_PROMETHEUS_PASSWORD": os.environ.get(
                "JUPYTERHUB_USAGE_QUOTAS_PROMETHEUS_PASSWORD"
            ),
        },
    }
    print(c.JupyterHub.services["usage-quota"])
