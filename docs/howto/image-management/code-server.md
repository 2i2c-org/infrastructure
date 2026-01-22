# Installing VS Code (code-server) Into An Image

Oftentimes administrators ask for the ability to run a VS Code instance on their JupyterHub. Whilst 2i2c cannot host VS Code Server as a service [due to the terms of the VS Code Server license][license], there are alternatives such as code-server that are not subject to these restrictions. As such, 2i2c recommends deploying code-server for communities that wish to run VS Code on their Hubs.

## Setting Up An Image

The `code-server` package is distributed by several packaging repositories, including `conda-forge` and the Debian/Ubuntu repositories. For most users, we'll recommend adding `code-server` to the Conda/Mamba environment definitions. In addition, we can use `jupyter-server-proxy` and `jupyter-vscode-proxy` to launch and proxy the code-server web service through the Jupyter Server application:

```{code} yaml
:emphasize-lines: 5,6,7
:linenos:
name: my-environment
channels:
  - conda-forge
dependencies:
  - code-server>=4.0
  - jupyter-vscode-proxy
  - jupyter-server-proxy
```

## Installing Extensions

Typically, users will want to install extensions on top of the base code-server instance. Whilst extensions in the [VS Code Marketplace](https://marketplace.visualstudio.com/VSCode) are not permitted to be used outside of Microsoft's VS Code products

> Microsoft prohibits the use of any non-Microsoft VS Code from accessing their marketplace.
>
> -- [VS Code Marketplace Terms of Use](https://aka.ms/vsmarketplace-ToU)

There is an alternative marketplace for open source extensions at https://open-vsx.org/. Since code-server 4.0.1, it is no longer required to specify OpenVSX as the default marketplace. Installing extensions is as simple as invoking `code-server` for each extension ID. This can be done inside the Dockerfile building the image, or using a [`postBuild`](https://repo2docker.readthedocs.io/en/latest/configuration/actions/#postbuild-run-code-after-installing-the-environment) script:

```bash
#!/bin/bash

set -euo pipefail

# Define packages
declare -a packages=( ms-python.python svelte.svelte-vscode )

# Install them
for package in "${packages[@]}"
do
  echo code-server --install-extension "${package}"
done
```

## Fixing Application Proxying

code-server ships with a built-in proxy for exposing local web-servers via the VSCode URL. However, in order to ensure that the activity from applications proxied by VS Code contribute to the activity metrics of the server, we want to use the jupyter-server-proxy mechanism for this. This can be done by defining the `VSCODE_PROXY_URI` environment variable, e.g. in the [`start`](https://repo2docker.readthedocs.io/en/latest/configuration/actions/#start-run-code-before-the-user-sessions-starts) file:

```bash
#!/bin/bash

set -euo pipefail

# Set proxy URI template
export VSCODE_PROXY_URI="../proxy/absolute/{{port}}/"

# Start true entrypoint
exec "$@"
```

[license]: https://code.visualstudio.com/docs/remote/vscode-server#_can-i-host-the-vs-code-server-as-a-service
