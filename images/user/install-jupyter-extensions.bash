#!/bin/bash
set -euo pipefail

jupyter labextension install --debug \
    @jupyterlab/server-proxy@2.1.2 \

# Install jupyter-contrib-nbextensions
jupyter contrib nbextension install --sys-prefix --symlink
