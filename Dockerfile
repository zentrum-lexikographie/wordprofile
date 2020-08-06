FROM python:3.8

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
  org.label-schema.name="zdl-wordprofile" \
  org.label-schema.description="A German Word Profile" \
  org.label-schema.url="https://git.zdl.org/zdl/wordprofile" \
  org.label-schema.vcs-ref=$VCS_REF \
  org.label-schema.vcs-url="https://git.zdl.org/zdl/wordprofile" \
  org.label-schema.vendor="Berlin-Brandenburg Academy of Sciences and Humanities" \
  org.label-schema.version=$VERSION \
  org.label-schema.schema-version="1.0"

#  cf. https://github.com/clab/dynet/#installation
RUN apt-get update && apt-get install -y \
  build-essential \
  cmake \
  mercurial \
  && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

# Pull dependencies
RUN pip install .
