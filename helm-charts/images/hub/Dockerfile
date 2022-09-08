# This image tag should match the dependent JupyterHub Helm chart's version as
# declared in basehub/Chart.yaml.
#
# If you make an update to this tag and the JupyterHub Helm chart's version,
# then commit those changes and then perform `chartpress --push` with your
# quay.io container registry credentials configured to have access to
# https://quay.io/repository/2i2c/pilot-hub.
#
# Note: if on macOs with M1, you need to run chartpress with docker buildx under the hood and specify
# the architecture to use.
# `chartpress --push --builder docker-buildx --platform linux/amd64`
# Ref: https://cloudolife.com/2022/03/05/Infrastructure-as-Code-IaC/Container/Docker/Docker-buildx-support-multiple-architectures-images/
#
FROM jupyterhub/k8s-hub:2.0.0-beta.1.git.5781.hc5adeae4

ENV CONFIGURATOR_VERSION ed7e3a0df1e3d625d10903ef7d7fd9c2fbb548db

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}

# Latest version comes with some breaking changes https://oauthenticator.readthedocs.io/en/latest/migrations.html#migrating-cilogonoauthenticator-to-version-15-0
RUN pip install --no-cache --upgrade git+https://github.com/jupyterhub/oauthenticator@6cf6599d99b47f99db3826ceaaedf467af14a05d

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
