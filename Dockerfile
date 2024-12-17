FROM python:3.12

RUN mkdir /app
WORKDIR /app

COPY requirements ./requirements

RUN pip install -U pip pip-tools setuptools &&\
    pip-sync requirements/base.txt requirements/api.txt

COPY . /app

CMD ["python", "-m", "wordprofile.apps.rest_api"]
