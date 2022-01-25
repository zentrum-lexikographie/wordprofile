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

RUN pip install -U pip setuptools wheel

COPY . /app
WORKDIR /app

# Pull dependencies
RUN pip install -r requirements.txt
RUN pip install .

# command to run on container start
ENTRYPOINT wp-xmlrpc --user wpuser --database wp_stage --spec spec/config.json --port 8080