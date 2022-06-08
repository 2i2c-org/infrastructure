import difflib
import sys
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

# Import colorama to colorize diff output, with a fallback incase colorama is not available
try:
    from colorama import Back, Fore, Style, init

    init()
except ImportError:  # Fallback so that the imported classes always exist

    class ColorFallback:
        __getattr__ = lambda self, name: ""

    Fore = Back = Style = ColorFallback()


# Function to colorize diff output for easier reading
def color_diff(diff):
    for line in diff:
        if line.startswith("+"):
            yield Fore.GREEN + line + Fore.RESET
        elif line.startswith("- "):
            yield Fore.RED + line + Fore.RESET
        elif line.startswith("^"):
            yield Fore.BLUE + line + Fore.RESET
        elif line.startswith("!"):
            yield Fore.YELLOW + line + Fore.RESET
        else:
            yield line


# Set up YAML Parser
yaml = YAML(typ="rt")
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


# Function to convert an dict generated from YAML into a string for comparison
def obj_to_yaml_str(obj, options={}):
    string_stream = StringIO()
    yaml.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    return output_str


keys_to_remove_from_jupyterhub_config = [
    ".custom.singleuserAdmin",
    ".custom.cloudResources",
    ".custom.docs_service",
    ".scheduling",
    ".prepuller",
    "",
]

# Get filepaths
root_path = Path(__file__).parent.parent
helm_charts_path = root_path.joinpath("helm-charts")
basehub_values_file = helm_charts_path.joinpath("basehub", "values.yaml")
daskhub_values_file = helm_charts_path.joinpath("daskhub", "values.yaml")
binderhub_values_file = helm_charts_path.joinpath("binderhub", "values.yaml")

# Read in values files
with open(basehub_values_file) as stream:
    basehub_values = yaml.load(stream)

with open(daskhub_values_file) as stream:
    daskhub_values = yaml.load(stream)

with open(binderhub_values_file) as stream:
    binderhub_values = yaml.load(stream)

# Compare dask-gateway values in the BinderHub and daskhub helm charts
# Raise an error if they differ
print("*** Comparing dask-gateway config ***")
daskhub_values_dask_gateway = obj_to_yaml_str(
    daskhub_values["dask-gateway"]
).splitlines(keepends=True)
binderhub_values_dask_gateway = obj_to_yaml_str(
    binderhub_values["dask-gateway"]
).splitlines(keepends=True)

diff = list(
    difflib.context_diff(
        binderhub_values_dask_gateway,
        daskhub_values_dask_gateway,
        fromfile=str(binderhub_values_file),
        tofile=str(daskhub_values_file),
    )
)

if "".join(diff) != "":
    diff = color_diff(diff)
    print("".join(diff))
    sys.exit(1)
else:
    print("*** All good! ***")

# Compare jupyterhub values in the BinderHub and daskhub helm charts
# Raise an error if they differ
print("*** Merging jupyterhub config from basehub and daskhub ***")
jupyterhub_config = (
    basehub_values["jupyterhub"] | daskhub_values["basehub"]["jupyterhub"]
)

print("*** Comparing jupyterhub config ***")
jupyterhub_config = obj_to_yaml_str(jupyterhub_config).splitlines(keepends=True)
binderhub_values_jupyterhub = obj_to_yaml_str(
    binderhub_values["binderhub"]["jupyterhub"]
).splitlines(keepends=True)

diff = list(
    difflib.context_diff(
        binderhub_values_jupyterhub,
        jupyterhub_config,
        fromfile=str(binderhub_values_file),
        tofile=f"{basehub_values_file} && {daskhub_values_file}",
    )
)

if "".join(diff) != "":
    diff = color_diff(diff)
    print("".join(diff))
    sys.exit(1)
else:
    print("*** All good! ***")
