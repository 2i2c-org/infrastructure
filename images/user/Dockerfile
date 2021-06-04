FROM buildpack-deps:focal-scm

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV NB_USER jovyan
ENV NB_UID 1000

ENV CONDA_DIR /opt/conda
ENV R_LIBS_USER /opt/r

# Explicitly add littler to PATH
# See https://github.com/conda-forge/r-littler-feedstock/issues/6
ENV PATH ${CONDA_DIR}/lib/R/library/littler/bin:${CONDA_DIR}/bin:$PATH

RUN adduser --disabled-password --gecos "Default Jupyter user" ${NB_USER}

# Create user owned R libs dir
# This lets users temporarily install packages
RUN mkdir -p ${R_LIBS_USER} && chown ${NB_USER}:${NB_USER} ${R_LIBS_USER}

# Install these without 'recommended' packages to keep image smaller.
# Useful utils that folks sort of take for granted
RUN apt-get update -qq --yes > /dev/null && \
    apt-get install --yes --no-install-recommends -qq \
        htop \
        less \
        man \
        nano \
        screen \
        tar \
        tmux \
        wget \
        vim \
        locales > /dev/null

RUN echo "${LC_ALL} UTF-8" > /etc/locale.gen && \
    locale-gen

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
RUN echo "deb https://cloud.r-project.org/bin/linux/ubuntu focal-cran40/" > /etc/apt/sources.list.d/cran.list

# Install R packages
# Our pre-built R packages from rspm are built against system libs in focal
# rstan takes forever to compile from source, and needs libnodejs
# So we install older (10.x) nodejs from apt rather than newer from conda
RUN apt-get update -qq --yes > /dev/null && \
    apt-get install --yes -qq \
    r-base \
    r-base-dev \
    r-recommended \
    r-cran-littler \
    nodejs \
    npm

# for nbconvert
RUN apt-get update -qq --yes && \
    apt-get install --yes -qq \
        pandoc \
        texlive-xetex \
        texlive-fonts-recommended > /dev/null

WORKDIR /home/jovyan

COPY install-miniforge.bash /tmp/install-miniforge.bash
RUN /tmp/install-miniforge.bash

# Needed by RStudio
RUN apt-get update -qq --yes && \
    apt-get install --yes --no-install-recommends -qq \
        psmisc \
        sudo \
        libapparmor1 \
        lsb-release \
        libclang-dev  > /dev/null

# Set path where R packages are installed
# Download and install rstudio manually
# Newer one has bug that doesn't work with jupyter-rsession-proxy
ENV RSTUDIO_URL https://download2.rstudio.org/server/bionic/amd64/rstudio-server-1.2.5042-amd64.deb
RUN curl --silent --location --fail ${RSTUDIO_URL} > /tmp/rstudio.deb && \
    dpkg -i /tmp/rstudio.deb && \
    rm /tmp/rstudio.deb

# Needed by many R libraries
# Picked up from https://github.com/rocker-org/rocker/blob/9dc3e458d4e92a8f41ccd75687cd7e316e657cc0/r-rspm/focal/Dockerfile
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
                   libgdal26 \
                   libgeos-3.8.0 \
                   libproj15 \
                   libudunits2-0 \
                   libxml2 \
                   libglpk-dev \
                   libgmp3-dev \
                   libcurl4-openssl-dev \
                   libgit2-dev \
                   libxml2-dev > /dev/null

# Needed by rJava library
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jdk > /dev/null && \
    R CMD javareconf

# Packages our users have requested.
# FFMPEG: https://github.com/2i2c-org/pilot/issues/5
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
                   ffmpeg > /dev/null

# R_LIBS_USER is set by default in /etc/R/Renviron, which RStudio loads.
# We uncomment the default, and set what we wanna - so it picks up
# the packages we install. Without this, RStudio doesn't see the packages
# that R does.
# Stolen from https://github.com/jupyterhub/repo2docker/blob/6a07a48b2df48168685bb0f993d2a12bd86e23bf/repo2docker/buildpacks/r.py
RUN sed -i -e '/^R_LIBS_USER=/s/^/#/' /etc/R/Renviron && \
    echo "R_LIBS_USER=${R_LIBS_USER}" >> /etc/R/Renviron

USER ${NB_USER}

COPY requirements.txt /tmp/

RUN python3 -m pip install -r /tmp/requirements.txt

# Set CRAN mirror to rspm before we install anything
COPY Rprofile.site /usr/lib/R/etc/Rprofile.site
# RStudio needs its own config
COPY rsession.conf /etc/rstudio/rsession.conf

# Install IRKernel
RUN r -e "install.packages('IRkernel', version='1.1.1')" && \
    r -e "IRkernel::installspec(prefix='${CONDA_DIR}')"

# Install R packages, cleanup temp package download location
COPY install.R /tmp/install.R
RUN /tmp/install.R && \
 	rm -rf /tmp/downloaded_packages/ /tmp/*.rds

# Set bash as shell in terminado.
ADD jupyter_notebook_config.py  ${CONDA_PREFIX}/etc/jupyter/
