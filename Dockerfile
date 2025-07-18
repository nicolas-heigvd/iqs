ARG DEBIAN_FRONTEND=noninteractive

FROM python:3.12-slim-bookworm AS build

ARG DEBIAN_FRONTEND

LABEL org.opencontainers.image.authors="Nicolas Blanc @ HEIG-VD"

# Create a new group and a new user with your UID/GID
RUN groupadd -g 1000 iqs
RUN useradd -u 1000 -g 1000 -m iqs

WORKDIR /app

RUN apt-get -yq update \
  && apt-get install -yq --fix-missing --no-install-recommends \
  build-essential \
  libgdal-dev \
  libx11-6 \
  libxrender1 \
  libxxf86vm1 \
  libxfixes3 \
  libxi6 \
  libxkbcommon-x11-0 \
  libsm6 \
  libgl1 \
  curl \
  unzip \
  git \
  jq \
  postgresql-client \
  && apt-get -yq autoremove --purge \
  && apt-get -yq autoclean \
  && ln -fs /usr/share/zoneinfo/Europe/Zurich /etc/localtime \
  && dpkg-reconfigure -f noninteractive tzdata

COPY requirements/*.in ./requirements/
#COPY src /app/

RUN python -m pip install --trusted-host pypi.python.org --upgrade pip \
  && pip install --trusted-host pypi.python.org --upgrade \
  setuptools \
  wheel \
  pip-tools \
  && for req_file in /app/requirements/*.in; do \
       pip-compile "${req_file}" 2> /dev/null; \
     done \
  && pip install --trusted-host pypi.python.org -r requirements/common.txt \
  && apt-get -yq autoremove --purge build-essential wget unzip git \
  && apt-get -yq autoclean \
  && echo "Image succcessfully build!"

