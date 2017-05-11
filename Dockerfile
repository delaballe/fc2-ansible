FROM alpine:3.5

MAINTAINER Cyril Gratecos cyril.gratecos@gamil.com

RUN apk add --update --no-cache \
      bash \
      gettext \
      openssh \
      git \
      python \
      python-dev \
      py-pip \
      py-yaml \
      libffi-dev \
      openssl-dev \
      build-base \
    && pip install --upgrade --no-cache-dir pip

RUN mkdir /fcu-ansible
COPY . /fcu-ansible
WORKDIR /fcu-ansible

RUN pip install --no-cache-dir -r requirement-pip
RUN pip install --no-cache-dir -r requirement-fcu-ansible

VOLUME /fcu-ansible/roles
VOLUME /fcu-ansible/playbooks
