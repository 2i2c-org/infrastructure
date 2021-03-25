# Should match the hub image used by version of chart in hub/requirements.yaml
# If that changes, this should be changed too!
FROM jupyterhub/k8s-hub:0.11.1-n298.hd9d7403b

ENV CONFIGURATOR_VERSION 746e7285af40b9bafd227dae3f2e41d1a631a301

RUN pip install --no-cache git+https://github.com/yuvipanda/jupyterhub-configurator@${CONFIGURATOR_VERSION}
