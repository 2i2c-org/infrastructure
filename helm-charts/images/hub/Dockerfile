# This image tag should match the dependent JupyterHub Helm chart's version as
# declared in basehub/Chart.yaml.
#
# If you make an update to this tag and the JupyterHub Helm chart's version,
# then first commit those changes.
# Then, from the `helm-charts` directory where the `chartpress.yaml` is located,
# perform `chartpress --push` with your quay.io container registry credentials
# configured to have access to https://quay.io/repository/2i2c/pilot-hub.
#
# Note: if on macOs with M1, you need to run chartpress with docker buildx under the hood and specify
# the architecture to use.
# `chartpress --push --builder docker-buildx --platform linux/amd64`
# Ref: https://cloudolife.com/2022/03/05/Infrastructure-as-Code-IaC/Container/Docker/Docker-buildx-support-multiple-architectures-images/
#
FROM jupyterhub/k8s-hub:3.0.0-beta.1
ARG REQUIREMENTS_FILE

COPY ${REQUIREMENTS_FILE} /tmp/

RUN pip install -r /tmp/${REQUIREMENTS_FILE}

USER root
RUN mkdir -p /usr/local/etc/jupyterhub-configurator

COPY jupyterhub_configurator_config.py /usr/local/etc/jupyterhub-configurator/jupyterhub_configurator_config.py
USER $NB_USER
