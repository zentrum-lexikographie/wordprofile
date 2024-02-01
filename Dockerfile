FROM python:3.10

RUN mkdir /app
WORKDIR /app

COPY . /app

RUN pip install pipenv
RUN pipenv install --categories="packages api build"


CMD ["python", "-m", "wordprofile.apps.rest_api"]
