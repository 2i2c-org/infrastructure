# This image tag should match the dependent JupyterHub Helm chart's version as
# declared in basehub/Chart.yaml.
#
# If you make an update to this tag and the JupyterHub Helm chart's version,
# then commit those changes and then perform `chartpress --push` with your
# quay.io container registry credentials configured to have access to
# https://quay.io/repository/2i2c/pilot-hub.
#
FROM jupyterhub/k8s-hub:1.1.3

ENV CONFIGURATOR_VERSION ed7e3a0df1e3d625d10903ef7d7fd9c2fbb548db

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
