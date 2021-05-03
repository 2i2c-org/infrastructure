# -- Project information -----------------------------------------------------

project = "2i2c Pilot Hubs Infrastructure"
copyright = "2020, 2i2c.org"
author = "2i2c.org"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.intersphinx",
    "sphinx_panels",
]

intersphinx_mapping = {
    "z2jh": ("https://zero-to-jupyterhub.readthedocs.io/en/latest/", None),
    "tc": ("https://team-compass.2i2c.org/en/latest/", None),
}

# -- MyST configuration ---------------------------------------------------
myst_enable_extensions = [
    "deflist",
    "colon_fence",
]

source_suffix = [".rst", ".md"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for MyST -------------------------------------------------
panels_add_bootstrap_css = False
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/2i2c-org/pilot-hubs",
    "use_issues_button": True,
    "use_repository_button": True,
}

# -- Custom scripts -----------------------------------------
# Pull latest list of communities served by pilot-hubs/
import requests
from yaml import safe_load
from ghapi.all import GhApi
from base64 import b64decode
import os
import pandas as pd
from pathlib import Path

# Grab the latest list of clusters defined in pilot-hubs/
api = GhApi(token=os.environ.get("GITHUB_TOKEN"))
clusters = api.repos.get_content("2i2c-org", "pilot-hubs", "config/hubs")
hub_list = []
for cluster_info in clusters:
    if "schema" in cluster_info['name']:
        continue
    # For each cluster, grab it's YAML w/ the config for each hub
    yaml = api.repos.get_content("2i2c-org", "pilot-hubs", cluster_info['path'])
    cluster = safe_load(b64decode(yaml['content']).decode())

    # For each hub in cluster, grab its metadata and add it to the list
    for hub in cluster['hubs']:
        config = hub['config']
        # Config is sometimes nested
        if 'base-hub' in config:
            hub_config = config['base-hub']['jupyterhub']
        else:
            hub_config = config['jupyterhub']
        # Domain can be a list
        if isinstance(hub['domain'], list):
            hub['domain'] = hub['domain'][0]

        hub_list.append({
            'name': hub_config['homepage']['templateVars']['org']['name'],
            'domain': f"[{hub['domain']}](https://{hub['domain']})",  
            "id": hub['name'],
            "template": hub['template'],
        })
df = pd.DataFrame(hub_list)
path_tmp = Path("tmp")
path_tmp.mkdir(exist_ok=True)
path_table = path_tmp / "hub-table.csv"
if not path_table.exists():
    df.to_csv(path_table, index=None)