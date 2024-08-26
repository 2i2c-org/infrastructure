# syntax = docker/dockerfile:1.3


# The build stage
# ---------------
# This stage is building Python wheels for use in later stages by using a base
# image that has more pre-requisites to do so, such as a C++ compiler.
#
FROM python:3.12-bullseye as build-stage

# Build wheels
#
# We set pip's cache directory and expose it across build stages via an
# ephemeral docker cache (--mount=type=cache,target=${PIP_CACHE_DIR}). We use
# the same technique for the directory /tmp/wheels.
#
COPY requirements.txt requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip wheel \
        --wheel-dir=/tmp/wheels \
        -r requirements.txt


# The final stage
# ---------------
#
FROM python:3.12-slim-bullseye as slim-stage
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends \
        tini \
 && rm -rf /var/lib/apt/lists/*

# install wheels built in the build stage
# --no-index ensures _only_ wheels from the build stage are installed
COPY requirements.txt /tmp/requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/tmp/wheels,target=/tmp/wheels \
    pip install \
        --no-index \
        --find-links=/tmp/wheels/ \
        -r /tmp/requirements.txt

WORKDIR /srv/aws-ce-grafana-backend

USER 65534
EXPOSE 8080
ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "flask", "--app=webserver", "run", "--host=0.0.0.0", "--port=8080"]
