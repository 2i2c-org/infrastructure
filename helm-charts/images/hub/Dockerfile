# This image tag should match the dependent JupyterHub Helm chart's version as
# declared in basehub/Chart.yaml.
#
# If you make an update to this tag and the JupyterHub Helm chart's version,
# then commit those changes and then perform `chartpress --push` with your
# quay.io container registry credentials configured to have access to
# https://quay.io/repository/2i2c/pilot-hub.
#
FROM jupyterhub/k8s-hub:1.1.3-n644.h35436cda

ENV CONFIGURATOR_VERSION ed7e3a0df1e3d625d10903ef7d7fd9c2fbb548db

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}

# Needed to install JupyterHub from source
USER root
RUN apt update --yes > /dev/null && apt install --yes --no-install-recommends nodejs npm > /dev/null
USER $NB_USER
# Until https://github.com/jupyterhub/jupyterhub/pull/3984 is merged
RUN pip install --upgrade git+https://github.com/meeseeksmachine/jupyterhub@72e4119e1a9f5fead690cb399dba36143d6d2ecc

# Latest version comes with some breaking changes https://oauthenticator.readthedocs.io/en/latest/migrations.html#migrating-cilogonoauthenticator-to-version-15-0
RUN pip install --no-cache --upgrade oauthenticator==15.0.1

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
