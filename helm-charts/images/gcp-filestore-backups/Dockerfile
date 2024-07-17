FROM python:3.12.4

USER root

# Install gcloud CLI
RUN apt-get update
RUN apt-get install apt-transport-https ca-certificates gnupg curl -y
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update -y && apt-get install google-cloud-sdk -y

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY gcp-filestore-backups.py /
