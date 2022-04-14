# -- Project information -----------------------------------------------------

project = "Infrastructure Guide"
copyright = "2020, 2i2c.org"
author = "2i2c.org"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_panels",
]

intersphinx_mapping = {
    "z2jh": ("https://zero-to-jupyterhub.readthedocs.io/en/latest/", None),
    "tc": ("https://team-compass.2i2c.org/en/latest/", None),
    "dc": ("https://docs.2i2c.org/en/latest/", None),
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
html_theme = "sphinx_2i2c_theme"
html_title = "Infrastructure Guide"
html_theme_options = {
    "repository_url": "https://github.com/2i2c-org/infrastructure",
    "use_issues_button": True,
    "use_repository_button": True,
}
html_static_path = ["_static"]
# Disable linkcheck for anchors because it throws false errors for any JS anchors
linkcheck_anchors = False
linkcheck_ignore = [
    "https://howard.cloudbank.2i2c.cloud*",  # Temporarily ignore because we've changed the hub name
    "https://github.com/organizations/2i2c-org/settings/applications/new",  # Only accessible to 2i2c-org members
    "https://docs.github.com",  # Gives 403 Forbidden errors
]


def setup(app):
    app.add_css_file("custom.css")


import subprocess
from pathlib import Path

import pandas as pd

# -- Custom scripts -----------------------------------------
# Pull latest list of communities served by infrastructure/
from yaml import safe_load


def render_hubs():
    # Grab the latest list of clusters defined in infrastructure/ explicitly ignoring
    # the test clusters in the ./tests directory
    clusters = [
        filepath
        for filepath in Path("../config/clusters").glob("**/*cluster.yaml")
        if "tests/" not in str(filepath)
    ]

    hub_list = []
    for cluster_info in clusters:
        cluster_path = cluster_info.parent
        if "schema" in cluster_info.name or "staff" in cluster_info.name:
            continue
        # For each cluster, grab it's YAML w/ the config for each hub
        yaml = cluster_info.read_text()
        cluster = safe_load(yaml)

        # Pull support chart information to populate fields (if it exists)
        support_files = cluster.get("support", {}).get("helm_chart_values_files", None)

        # Incase we don't find any Grafana config, use an empty string as default
        grafana_url = ""

        # Loop through support files, look for Grafana config, and grab the URL
        if support_files is not None:
            for support_file in support_files:
                with open(cluster_path.joinpath(support_file)) as f:
                    support_config = safe_load(f)

                grafana_url = (
                    support_config.get("grafana", {})
                    .get("ingress", {})
                    .get("hosts", "")
                )
                # If we find a grafana url, set it here and break the loop, we are done
                if isinstance(grafana_url, list):
                    grafana_url = grafana_url[0]
                    grafana_url = f"[{grafana_url}](http://{grafana_url})"
                    break

        # For each hub in cluster, grab its metadata and add it to the list
        for hub in cluster["hubs"]:
            # Domain can be a list
            if isinstance(hub["domain"], list):
                hub["domain"] = hub["domain"][0]

            hub_list.append(
                {
                    # Fallback to name if display_name isn't available
                    "name": hub.get("display_name", "name"),
                    "domain": f"[{hub['domain']}](https://{hub['domain']})",
                    "id": hub["name"],
                    "hub_type": hub["helm_chart"],
                    "grafana": grafana_url,
                }
            )
    df = pd.DataFrame(hub_list)
    path_tmp = Path("tmp")
    path_tmp.mkdir(exist_ok=True)
    path_table = path_tmp / "hub-table.csv"
    df.to_csv(path_table, index=None)


def render_tfdocs():
    tf_path = Path("../terraform")
    # Output path is relative to terraform directory
    output_path = Path("../docs/reference/terraform.md")

    # hub_type for output file is in ../terraform/.terraform-docs.yml
    subprocess.check_call(
        [
            "terraform-docs",
            "markdown",
            f"--output-file={output_path}",
            f'--config={str(tf_path / ".terraform-docs.yml")}',
            str(tf_path),
        ]
    )


render_hubs()
render_tfdocs()
