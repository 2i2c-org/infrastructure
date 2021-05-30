# Should match the hub image used by version of chart in hub/requirements.yaml
# If that changes, this should be changed too!
FROM jupyterhub/k8s-hub:1.0.0-beta.1

ENV CONFIGURATOR_VERSION ed7e3a0df1e3d625d10903ef7d7fd9c2fbb548db

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}

ENV OAUTHENTICATOR_VERSION 878cec5f3008d8502256253e6d155e8a8ed0cd98

RUN pip install --no-cache git+https://github.com/jupyterhub/oauthenticator@${OAUTHENTICATOR_VERSION}

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
