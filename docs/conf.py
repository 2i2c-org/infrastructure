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
from yaml import safe_load
import pandas as pd
from pathlib import Path
import subprocess

def render_hubs():
    # Grab the latest list of clusters defined in pilot-hubs/
    clusters = Path("../config/hubs").glob("*")
    # Add list of repos managed outside pilot-hubs
    hub_list = [{
        'name': 'University of Toronto',
        'domain': 'jupyter.utoronto.ca',
        'id': 'utoronto',
        'template': 'base-hub ([deployment repo](https://github.com/utoronto-2i2c/jupyterhub-deploy/))'
    }]
    for cluster_info in clusters:
        if "schema" in cluster_info.name:
            continue
        # For each cluster, grab it's YAML w/ the config for each hub
        yaml = cluster_info.read_text()
        cluster = safe_load(yaml)

        # For each hub in cluster, grab its metadata and add it to the list
        for hub in cluster['hubs']:
            config = hub['config']
            # Config is sometimes nested
            if 'basehub' in config:
                hub_config = config['basehub']['jupyterhub']
            else:
                hub_config = config['jupyterhub']
            # Domain can be a list
            if isinstance(hub['domain'], list):
                hub['domain'] = hub['domain'][0]

            hub_list.append({
                'name': hub_config['custom']['homepage']['templateVars']['org']['name'],
                'domain': f"[{hub['domain']}](https://{hub['domain']})",
                "id": hub['name'],
                "template": hub['template'],
            })
    df = pd.DataFrame(hub_list)
    path_tmp = Path("tmp")
    path_tmp.mkdir(exist_ok=True)
    path_table = path_tmp / "hub-table.csv"
    df.to_csv(path_table, index=None)


def render_tfdocs():
    tf_path = Path('../terraform')
    # Output path is relative to terraform directory
    output_path = Path('../docs/reference/terraform.md')

    # Template for output file is in ../terraform/.terraform-docs.yml
    subprocess.check_call([
        'terraform-docs', 'markdown',
        f"--output-file={output_path}",
        f'--config={str(tf_path / ".terraform-docs.yml")}',
        str(tf_path)
    ])



render_hubs()
render_tfdocs()