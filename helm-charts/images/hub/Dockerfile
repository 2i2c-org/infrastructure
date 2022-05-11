# This image tag should match the dependent JupyterHub Helm chart's version as
# declared in basehub/Chart.yaml.
#
# If you make an update to this tag and the JupyterHub Helm chart's version,
# then commit those changes and then perform `chartpress --push` with your
# quay.io container registry credentials configured to have access to
# https://quay.io/repository/2i2c/pilot-hub.
#
FROM jupyterhub/k8s-hub:1.2.0

ENV CONFIGURATOR_VERSION ed7e3a0df1e3d625d10903ef7d7fd9c2fbb548db

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}


# Install newer version of jupyterhub-kubespawner, to bring in https://github.com/jupyterhub/kubespawner/pull/525
# https://github.com/2i2c-org/infrastructure/issues/1103 is happening frequently enough
# z2jh 1.2.x ships with kubespawner 1.1.0, so we just do a little bump
RUN pip install --no-cache --upgrade jupyterhub-kubespawner==1.1.2

# Brings in https://github.com/jupyterhub/oauthenticator/pull/498
RUN pip install --no-cache --upgrade git+https://github.com/jupyterhub/oauthenticator@d189037fe6b57453a3ae733a60740c50f241e713

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
