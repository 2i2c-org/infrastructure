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
    "sphinx_design",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.jquery",
]

intersphinx_mapping = {
    "z2jh": ("https://zero-to-jupyterhub.readthedocs.io/en/latest/", None),
    "tc": ("https://team-compass.2i2c.org", None),
    "dc": ("https://docs.2i2c.org", None),
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

# -- Custom scripts -----------------------------------------
subprocess.run(
    ["python", "helper-programs/generate-general-info-table-about-hubs.py"], check=True
)
subprocess.run(["python", "helper-programs/generate-hub-features-table.py"], check=True)
