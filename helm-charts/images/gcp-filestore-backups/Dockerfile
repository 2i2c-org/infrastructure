FROM python:3.12.4

USER root

# Install gcloud CLI
RUN apt-get update
RUN apt-get install apt-transport-https ca-certificates gnupg curl -y
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
RUN apt-get update -y && apt-get install google-cloud-sdk -y

# chartpress.yaml defines multiple hub images differentiated only by a
# requirements.txt file with dependencies, this build argument allows us to
# reuse this Dockerfile for all images.
ARG REQUIREMENTS_FILE
COPY ${REQUIREMENTS_FILE} /tmp/

COPY gcp-filestore-backups.py /
