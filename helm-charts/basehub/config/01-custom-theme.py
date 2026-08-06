# adds a JupyterHub template path and updates template variables

from z2jh import get_config

c.JupyterHub.template_paths.insert(0, "/usr/local/share/jupyterhub/custom_templates")
c.JupyterHub.template_vars.update(
    {"custom": get_config("custom.homepage.templateVars")}
)
